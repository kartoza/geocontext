from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import pytz
import requests
import threading

from django.contrib.gis.gdal.error import SRSException
from django.contrib.gis.geos import Point
from django.http import QueryDict
from owslib.wms import WebMapService
from xml.dom import minidom

from geocontext.models.csr import CSR
from geocontext.models.cache import Cache
from geocontext.utilities import (
    convert_coordinate,
    dms_dd,
    find_geometry_in_xml,
    get_bbox,
    parse_gml_geometry,
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
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(retrieve_external_csr, util_arg_list):
            new_result_list.append(result)
    return new_result_list


def retrieve_external_csr(util_arg: namedtuple) -> namedtuple:
    """Fetch data and loads into CSRUtils instance
    using threadlocal request session if found.

    :param namedtuple: (group_key, csr_util)
    :type util_arg: namedtuple(int, CSRUtils)

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
        """Load threadsafe csr object. Transform user query to CSR geometry

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
        self.cache_url = None
        self.value = None
        csr = None

        self.x = x
        self.y = y
        self.srid_in = srid_in
        self.generalize_point()
        self.geometry = self.point

    def generalize_point(self) -> Point:
        """Generalize coordinate to the registry instance geometry.

        Converts DMS (degree:minute:second:direction) to decimal degree.
        Converts to SRID of the context registry
        Removes extreme precision to improve point cache hits.
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
                    raise ValueError('Coordinate parse failed: {coord}. Require DD/DMS.')
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
                raise ValueError(f"SRID: '{self.srid_in}' not valid")

        # TODO Round smartly after projection using base data raster resolution
        # if self.query_type == ServiceDefinitions.WMS:
        #    if self.resolution:
        #        Calculate decimals depending on base resolution
        #        decimals = (1m = 5, 10m = 4, 100m = 3, 1000m = 2, 10000m = 1)

        decimals = 4
        x_round = Decimal(self.point.x).quantize(Decimal('0.' + '0' * decimals))
        y_round = Decimal(self.point.y).quantize(Decimal('0.' + '0' * decimals))
        self.point = Point(float(x_round), float(y_round), srid=self.srid)

    def retrieve_value(self) -> bool:
        """Load context value. All exception / null values handled here.

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
        except Exception as e:
            LOGGER.error(f"'{self.csr_key}' url failed: {self.cache_url} with: {e}")
            self.value = None

    def request_content(self, retries: int = 0) -> requests:
        """Get request content from cache url in request session

        :return: URL to do query.
        :rtype: unicode
        """
        session = get_session()
        try:
            with session.get(self.cache_url) as response:
                if response.status_code == 200:
                    return response.content
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"'{self.csr_key}' url failed: {self.cache_url} with: {e}")
            return None

    def fetch_wms(self):
        """Fetch WMS value
        """
        wms = WebMapService(self.url, self.service_version)
        response = wms.getfeatureinfo(
            layers=[self.layer_typename],
            bbox=get_bbox(self.point),
            size=[101, 101],
            xy=[50, 50],
            srs='EPSG:' + str(self.point.srid),
            info_format='application/vnd.ogc.gml'
        )
        xmldoc = minidom.parseString(response.read())
        value_dom = xmldoc.getElementsByTagName(self.result_regex)[0]
        self.value = value_dom.childNodes[0].nodeValue
        self.cache_url = response.geturl()

    def fetch_wfs(self):
        """Fetch WFS value
        """
        parameters = {
            'SERVICE': 'WFS',
            'REQUEST': 'DescribeFeatureType',
            'VERSION': self.service_version,
            'TYPENAME': self.layer_typename
        }
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            self.cache_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.cache_url = f'{self.url}?{query_dict.urlencode()}'
        geo_name, geo_type = find_geometry_in_xml(self.request_content())
        if 'Polygon' in geo_type:
            layer_filter = (
                '<Filter xmlns="http://www.opengis.net/ogc" '
                'xmlns:gml="http://www.opengis.net/gml"> '
                f'<Intersects><PropertyName>{geo_name}</PropertyName>'
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
                'PROPERTYNAME': f'({self.result_regex[4:]})',
                'MAXFEATURES': 1,
                'OUTPUTFORMAT': 'GML3',
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                self.cache_url = f'{self.url}&{query_dict.urlencode()}'
            else:
                self.cache_url = f'{self.url}?{query_dict.urlencode()}'
            if ':' not in self.layer_typename:
                self.cache_url += f'&SRSNAME={self.point.srid}'
            gml_string = self.request_content()

        else:

            bbox = get_bbox(self.point)
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'OUTPUTFORMAT': 'GML3',
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                self.cache_url = f'{self.url}&{query_dict.urlencode()}'
            else:
                self.cache_url = f'{self.url}?{query_dict.urlencode()}'
            if ':' not in self.layer_typename:
                self.cache_url += f'&SRSNAME={self.point.srid}'
            self.cache_url += '&BBOX=' + bbox
            gml_string = self.request_content()

        xmldoc = minidom.parseString(gml_string)
        value_dom = xmldoc.getElementsByTagName(self.result_regex)[0]
        self.value = value_dom.childNodes[0].nodeValue
        new_geometry = parse_gml_geometry(gml_string, self.layer_typename)
        if new_geometry is not None:
            self.geometry = new_geometry
            if not self.geometry.srid:
                self.geometry.srid = self.point.srid

    def fetch_arcrest(self):
        """Fetch ArcRest value
        """
        bbox = get_bbox(self.point)
        parameters = {
            'f': 'json',
            'geometryType': 'esriGeometryPoint',
            'geometry': f'{{{{x: {self.point.x}, y: {self.point.y}}}}}',
            'layers': self.layer_typename,
            'imageDisplay': '581,461,96',
            'tolerance': '10',
        }
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            self.cache_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.cache_url = f'{self.url}/identify?{query_dict.urlencode()}'
            self.cache_url += f'&mapExtent={bbox}'
        json_document = json.loads(self.request_content())
        self.value = json_document['results'][0][self.result_regex]

    def fetch_placename(self):
        """Fetch Placename value
        """
        parameters = {
            'lat': str(self.point.y),
            'lng': str(self.point.x),
            'username': str(self.api_key),
        }
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            self.cache_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.cache_url = f'{self.url}?{query_dict.urlencode()}'
        json_document = json.loads(self.request_content())
        self.value = json_document['geonames'][0][self.result_regex]
