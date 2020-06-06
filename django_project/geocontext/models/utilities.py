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
from django.http import QueryDict

from geocontext.models.csr import CSR
from geocontext.models.cache import Cache
from geocontext.utilities import (
    convert_coordinate,
    dms_dd,
    get_bbox,
    ServiceDefinitions,
    parse_dms
)

LOGGER = logging.getLogger(__name__)
thread_local = threading.local()
UtilArg = namedtuple('UtilArgs', ['group_key', 'csr_util'])


def get_csr(csr_key) -> CSR:
    """Returns context service registry instance or raise error

    :raises KeyError: If registry not found

    :return: context service registry
    :rtype: CSR
    """
    try:
        return CSR.objects.get(key=csr_key)
    except CSR.DoesNotExist:
        raise KeyError(f'Service Registry not Found for: {csr_key}')


def create_cache(csr_util) -> Cache:
    """Add context value to cache

    :param csr_util: CSRUtils instance
    :type csr_util: CSRUtils

    :return: Context cache instance
    :rtype: Cache
    """
    csr = get_csr(csr_util.csr_key)
    expired_time = (datetime.utcnow() + timedelta(seconds=csr.time_to_live))
    expired_time = expired_time.replace(tzinfo=pytz.UTC)
    cache = Cache(csr=csr, name=csr.key, value=csr_util.value, expired_time=expired_time)
    if csr_util.cache_url:
        cache.source_uri = csr_util.cache_url
    if csr_util.geometry:
        cache.set_geometry_field(csr_util.geometry)
    cache.save()
    cache.refresh_from_db()
    return cache


def retrieve_cache(csr_util) -> Cache:
    """Try to retrieve context from point.

    :param csr_util: CSRUtils instance
    :type csr_util: CSRUtils

    :returns: cache on None
    :rtype: cache or None
    """
    return
    caches = Cache.objects.filter(csr=get_csr(csr_util.csr_key))
    for cache in caches:
        if cache.geometry and cache.geometry.contains(csr_util.point):
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            is_expired = current_time > cache.expired_time
            if is_expired:
                cache.delete()
                break
            else:
                return cache


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
    """Threadsafe context service registry model object + utility methods.
    """
    def __init__(self, csr_key: str, x: float, y: float, srid_in: int = 4326):
        """Load object. Transform user query to CSR geometry.

        Init method calls ORM so not threadsafe and should be done before async logic

        :param csr_key: csr_key
        :type csr_key: str

        :param x: (longitude)
        :type x: float

        :param y: Y (latitude)
        :type y: float

        :param srid: SRID (default=4326).
        :type srid: int
        """
        csr = get_csr(csr_key)
        self.csr_key = csr_key
        self.query_type = csr.query_type
        self.service_version = csr.service_version
        self.layer_typename = csr.layer_typename
        self.result_regex = csr.result_regex
        self.api_key = csr.api_key
        self.url = csr.url
        self.srid = csr.srid
        self.search_dist = csr.search_dist
        self.cache_url = None
        self.value = None
        csr = None

        # Layer names either equals result_regex or come after ":" in regex (geoserver)
        try:
            self.layer_name = self.result_regex.split(":")[1]
        except IndexError:
            self.layer_name = self.result_regex

        # Geometry defaults to query point - cache hits at least search_dist from point
        self.x = x
        self.y = y
        self.srid_in = srid_in
        self.load_point()
        self.geometry = self.point

    def load_point(self) -> Point:
        """Generalize coordinate to the registry instance geometry.

        Converts DMS (degree:minute:second:direction) to decimal degree.
        Converts to SRID of the context registry
        Default precision for is 4 decimals (~10m)

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
        """Load context value. All exception logging / null values handled here.

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
            "BBOX": get_bbox(self.point),
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
        }
        json_response = self.request_data(parameters)

        try:
            self.value = json_response["features"][0]["properties"][self.layer_name]
        except IndexError:
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'OUTPUTFORMAT': 'application/json',
            }
            bbox = get_bbox(self.point)
            json_response = self.request_data(parameters, append=f'&BBOX={bbox}')
            self.value = json_response["features"][0]["properties"][self.layer_name]

        # Add new geometry only if found
        if self.value is not None:
            try:
                new_geometry = json_response["features"][0]["geometry"]
                if new_geometry is not None:
                    self.geometry = GEOSGeometry(str(new_geometry))
                    self.geometry.srid = self.point.srid
            except IndexError:
                pass

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
        }
        bbox = get_bbox(self.point)
        bbox_str = f'&mapExtent={bbox}'
        json_response = self.request_data(parameters, query='/identify?', append=bbox_str)
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

    def request_data(
            self, parameters: dict, query: str = "?", append: str = None) -> dict:
        """Generates final query URL and fetches data.

        :param parameters: parameters to urlencode
        :type parameters: dict
        :param query: Url query delimiter
        :type query: str (default '?')
        :param append: additional string to append to url
        :type append: str
        :return: json response
        :rtype: dict
        """
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            query_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            query_url = f'{self.url}{query}{query_dict.urlencode()}'

        if append is not None:
            query_url += append

        # Only add SRS if there is no workspace
        if ':' not in self.layer_typename:
            query_url += f'&SRSNAME={self.point.srid}'

        session = get_session()
        with session.get(query_url) as response:
            if response.status_code == 200:
                self.cache_url = query_url
                return json.loads(response.content)
