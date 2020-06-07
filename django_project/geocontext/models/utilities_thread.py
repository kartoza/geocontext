""" Depreciated duplicate of utilities that uses threading instead of async.
Async with aoihttp speedups is more reliable than threading and shares a single session
Threading requires uwsgi config - which has a performance impact:
uwsgi.config
enable-threads = True
threads = 20
processes = 4
"""

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import logging
import pytz
import requests
import threading

from django.contrib.gis.gdal.error import SRSException
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import Distance
from django.http import QueryDict

from geocontext.models.csr import CSR
from geocontext.models.cache import Cache
from geocontext.utilities import (
    convert_2d_to_3d,
    convert_coordinate,
    dms_dd,
    get_bbox,
    ServiceDefinitions,
    parse_dms
)

LOGGER = logging.getLogger(__name__)
thread_local = threading.local()
UtilArg = namedtuple('UtilArgs', ['group_key', 'csr_util'])


def create_cache(csr_util) -> Cache:
    """Add context value to cache

    :param csr_util: CSRUtils instance
    :type csr_util: CSRUtils

    :return: Context cache instance
    :rtype: Cache
    """
    csr = CSR.objects.get(key=csr_util.csr_key)
    expired_time = (datetime.utcnow() + timedelta(seconds=csr.time_to_live))
    expired_time = expired_time.replace(tzinfo=pytz.UTC)
    cache = Cache(csr=csr, name=csr.key, value=csr_util.value, expired_time=expired_time)
    if csr_util.cache_url:
        cache.source_uri = csr_util.cache_url
    if csr_util.geometry:
        if csr_util.geometry.hasz:
            cache.geometry = csr_util.geometry
        else:
            cache.geometry = convert_2d_to_3d(csr_util.geometry)
    cache.save()
    cache.refresh_from_db()
    return cache


def retrieve_cache(csr_util) -> Cache:
    """Try to retrieve csr cache from query point input.
    Filters for search distance and expiry date.

    :param csr_util: CSRUtils instance
    :type csr_util: CSRUtils

    :returns: cache on None
    :rtype: cache or None
    """
    current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
    csr = CSR.objects.get(key=csr_util.csr_key)
    caches = Cache.objects.filter(
        csr=csr,
        expired_time__lte=current_time,
        geometry__distance_lte=(csr_util.point, Distance(m=csr_util.search_dist))
    )
    # Only expect one cache hit (there may be edge cases) - returns None if empty
    return caches.first()


def thread_retrieve_external(util_arg_list: list) -> list:
    """Threading master function for loading external service data

    :param util_arg_list: List with Registry util argument tuples
    :type util_arg_list: CSRUtils

    :return: list of threading tuple results
    :rtype: list
    """
    new_result_list = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(retrieve_external_csr, util_arg_list):
            new_result_list.append(result)
    return new_result_list


def retrieve_external_csr(util_arg: namedtuple) -> namedtuple:
    """Fetch data and loads into CSRUtils instance
    using threadlocal request session if found.

    :param namedtuple: (group_key, csr_util)
    :type util_arg: namedtuple(str, CSRUtils)

    :return: (group_key and CSRUtils)
    :rtype: namedtuple or None
    """
    util_arg.csr_util.retrieve_value()
    return util_arg


def get_session() -> thread_local:
    """Get thread local request session"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


class CSRUtils():
    """Async/Threadsafe context service registry model mock object + utility methods.
    Init method calls ORM / blocking functions so should be done before async logic
    """
    def __init__(
        self, csr_key: str, x: float, y: float, srid_in: int = 4326, dist: float = 10.0):
        """Load object. Prepare geometry. This __init__ is async blocking.

        :param csr_key: csr_key
        :type csr_key: str

        :param x: (longitude)
        :type x: float

        :param y: Y (latitude)
        :type y: float

        :param srid: SRID (default=4326).
        :type srid: int

        :param dist: Search distance query overide csr (default=10.0).
        :type dist: int
        """
        csr = CSR.objects.get(key=csr_key)
        self.csr_key = csr_key
        self.query_type = csr.query_type
        self.service_version = csr.service_version
        self.layer_typename = csr.layer_typename
        self.result_regex = csr.result_regex
        self.api_key = csr.api_key
        self.url = csr.url
        self.srid = csr.srid
        self.cache_url = None
        self.value = None

        # Search distance query overrides csr in model - else default 10m
        if dist == 10.0 and csr.search_dist is not None:
            self.search_dist = csr.search_dist
        else:
            self.search_dist = dist

        # Layer names either equals result_regex after workspace (":")
        try:
            self.layer_name = self.result_regex.split(":")[1]
        except IndexError:
            self.layer_name = self.result_regex

        # Prepare coordinates
        self.x = x
        self.y = y
        self.srid_in = srid_in
        self.load_point()

        # Geometry defaults to query point - cache hits at least search_dist from point
        self.geometry = self.point

        # Calculate bbox - not async func and be blocking so do in __init__
        self.bbox = get_bbox(self.point)

        # Remove ORM model from instance object for in case...
        csr = None

    def load_point(self) -> Point:
        """Transform coordinate to the registry instance srid in decimal degrees.

        Converts DMS (Split by °,',", or :) to decimal degree.
        Converts to SRID of the context registry

        :raises ValueError: If coordinate cannot be parsed

        :return: point
        :rtype: Point
        """
        # Parse Coordinate try DD / otherwise DMS
        for coord_attr_name in ['x', 'y']:
            coord = getattr(self, coord_attr_name)
            try:
                coord_dd = float(coord)
            except ValueError:
                try:
                    degrees, minutes, seconds = parse_dms(coord)
                    coord_dd = dms_dd(degrees, minutes, seconds)
                except ValueError:
                    raise ValueError(f"Coord parse for {self.csr_key} failed: {coord}.")
            setattr(self, coord_attr_name, coord_dd)

        # Parse srid and create point in crs srid
        try:
            self.srid_in = int(self.srid_in)
            self.point = Point(self.x, self.y, srid=self.srid_in)
        except ValueError:
            raise ValueError(f"SRID: '{self.srid_in}' not valid")

        if self.srid_in != self.srid:
            try:
                self.point = convert_coordinate(self.point, self.srid)
            except SRSException:
                raise ValueError(f"SRID: '{self.srid_in}' not valid for {self.csr_key}")

    def retrieve_value(self) -> bool:
        """Load context value. All exception / logging / null values handled here.

        :returns: success
        :rtype: bool
        """
        try:
            if self.query_type == ServiceDefinitions.WMS:
                self.fetch_wms()
            elif self.query_type == ServiceDefinitions.WFS:
                self.fetch_wfs()
            elif self.query_type == ServiceDefinitions.ARCREST:
                self.fetch_arcrest()
            elif self.query_type == ServiceDefinitions.PLACENAME:
                self.fetch_placename()
            else:
                LOGGER.error(f"'{self.query_type}' not implimented for {self.csr_key}")
                self.value = None
        except Exception as e:
            LOGGER.error(f"{self.cache_url} failed for: {self.csr_key} with: {e}")
            self.value = None

    def fetch_wms(self):
        """Fetch WMS value
        """
        parameters = {
            "SERVICE": self.query_type,
            "LAYERS": self.layer_typename,
            "QUERY_LAYERS": self.layer_typename,
            "BBOX": self.bbox,
            "WIDTH": 11,
            "HEIGHT": 11,
            "INFO_FORMAT": 'application/json',
            "FEATURE_COUNT": 1
        }
        if self.service_version in ['1.0.0', '1.1.0']:
            parameters['REQUEST'] = 'feature_info'
            parameters['SRS'] = 'EPSG:' + str(self.point.srid)
            parameters['X'] = 5
            parameters['Y'] = 5
        else:
            parameters['REQUEST'] = 'GetFeatureInfo'
            parameters['CRS'] = 'EPSG:' + str(self.point.srid)
            parameters['I'] = 5
            parameters['j'] = 5

        json_response = self.request_data(parameters)
        self.value = json_response["features"][0]["properties"][self.layer_name]

    def fetch_wfs(self):
        """Fetch WFS value - Try intersect else buffer with search distance
        """
        layer_filter = (
            '<Filter xmlns="http://www.opengis.net/ogc" '
            'xmlns:gml="http://www.opengis.net/gml"> '
            f'<Intersects><PropertyName>geom</PropertyName>'
            f'<gml:Point srsName="EPSG:{self.point.srid}">'
            f'<gml:coordinates>{self.point.x},{self.point.y}'
            '</gml:coordinates></gml:Point></Intersects></Filter>'
        )
        parameters = {
            'SERVICE': 'WFS',
            'REQUEST': 'GetFeature',
            'VERSION': self.service_version,
            'TYPENAME': self.layer_typename,
            'FILTER': layer_filter,
            'PROPERTYNAME': f'({self.layer_name})',
            'MAXFEATURES': 1,
            'OUTPUTFORMAT': 'application/json',
            'SRSNAME': self.point.srid
        }

        json_response = self.request_data(parameters)
        if len(json_response["features"]) > 0:
            self.value = json_response["features"][0]["properties"][self.layer_name]
        else:
            LOGGER.info(f"WFS intersect filter failed for: {self.csr_key} - attempt bbox")
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'OUTPUTFORMAT': 'application/json',
                'SRSNAME': self.point.srid,
                'BBOX': self.bbox
            }
            json_response = self.request_data(parameters)
            self.value = json_response["features"][0]["properties"][self.layer_name]

        # Add new geometry only if found and don't raise error if geometry isn't found
        if self.value is not None:
            try:
                new_geometry = json_response["features"][0]["geometry"]
                if new_geometry is not None:
                    self.geometry = GEOSGeometry(str(new_geometry))
                    self.geometry.srid = self.point.srid
            except IndexError:
                LOGGER.error(f"No geometry found for: {self.csr_key}")

    def fetch_arcrest(self):
        """Fetch ArcRest value
        """
        parameters = {
            'f': 'json',
            'geometryType': 'esriGeometryPoint',
            'geometry': f'{{{{x: {self.point.x}, y: {self.point.y}}}}}',
            'layers': self.layer_typename,
            'imageDisplay': '581,461,96',
            'tolerance': '10',
            'mapExtent': self.bbox
        }
        json_response = self.request_data(parameters, query='/identify?')
        self.value = json_response['results'][0][self.layer_name]

    def fetch_placename(self):
        """Fetch Placename value
        """
        parameters = {
            'lat': str(self.point.y),
            'lng': str(self.point.x),
            'username': str(self.api_key),
        }
        json_response = self.request_data(parameters)
        self.value = json_response['geonames'][0][self.layer_name]

    def request_data(self, parameters: dict, query: str = "?") -> dict:
        """Generates final query URL and fetches data.

        :param parameters: parameters to urlencode
        :type parameters: dict

        :param query: Url query delimiter
        :type query: str (default '?')

        :return: json response
        :rtype: dict
        """
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            query_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            query_url = f'{self.url}{query}{query_dict.urlencode()}'

        session = get_session()
        with session.get(query_url) as response:
            if response.status_code == 200:
                self.cache_url = query_url
                return json.loads(response.content)
