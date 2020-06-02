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


def thread_retrieve_external(util_arg_list: list) -> list:
    """Threading master function for loading external service data

    :param util_arg_list: List with Registry util argument tuples
    :type util_arg_list: CSRUtils

    :return: list of threading tuple results
    :rtype: list
    """
    new_result_list = []
    with ThreadPoolExecutor() as executor:
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
    """Mock context service registry model object + utility methods.
    Threadsafe - only __init__, get_ & create_cache
    access DB but does not store any connection/querysets.
    """
    def __init__(self, csr_key: str, x: str, y: str, srid: int = 4326):
        """Tools to load mock csr.

        :param csr_key: csr_key
        :type csr_key: int

        :param x: (longitude)
        :type x: float

        :param y: Y (latitude)
        :type y: float

        :param srid: SRID (default=4326).
        :type srid: int
        """
        self.csr_key = csr_key
        csr = self.get_csr()
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
        self.srid_in = srid
        self.generalize_point()
        self.geometry = self.point

    def get_csr(self) -> CSR:
        """Returns context service registry instance

        :raises KeyError: If registry not found

        :return: context service registry
        :rtype: CSR
        """
        try:
            return CSR.objects.get(key=self.csr_key)
        except CSR.DoesNotExist:
            raise KeyError(f'Service Registry not Found for: {self.csr_key}')

    def generalize_point(self) -> Point:
        """Generalize coordinate to the registry instance format.

        Converts ':' delimited degree, minute, second to decimal degree.
        Converts to SRID of the context registry
        Removes extreme precision to improve point cache hits.
        Default precision for is 4 decimals (~10m)

        :raises ValueError: If coordinate cannot be generalized

        :return: point
        :rtype: Point
        """
        # Parse Coordinate try DD / otherwise DMS
        for coord in ['x', 'y']:
            try:
                coord_dd = float(getattr(self, coord))
            except ValueError:
                try:
                    degrees, minutes, seconds = parse_dms(getattr(self, coord))
                    coord_dd = dms_dd(degrees, minutes, seconds)
                except ValueError:
                    raise ValueError('Coordinate parse failed: {coord}. Require DD/DMS.')
            setattr(self, coord, coord_dd)

        self.point = Point(self.x, self.y, srid=self.srid)

        if self.point.srid != self.srid:
            try:
                self.point = convert_coordinate(self.point, self.srid)
            except SRSException:
                raise ValueError(f"SRID: '{self.point.srid}' not valid")

        # Set precision after projection
        # if self.resolution:
            # Calculate decimals depending on base resolution
            # 1m = 5, 10m = 4, 100m = 3, 1000m = 2, 10000m = 1
        decimals = 4
        x_round = Decimal(self.point.x).quantize(Decimal('0.' + '0' * decimals))
        y_round = Decimal(self.point.y).quantize(Decimal('0.' + '0' * decimals))
        self.point = Point(float(x_round), float(y_round), srid=self.srid)

    def create_cache(self) -> Cache:
        """Add context value to cache

        :return: Context cache instance
        :rtype: Cache
        """
        csr = self.get_csr()
        expired_time = (datetime.utcnow() + timedelta(seconds=csr.time_to_live))
        expired_time = expired_time.replace(tzinfo=pytz.UTC)
        cache = Cache(csr=csr, name=csr.key, value=self.value, expired_time=expired_time)
        csr = None
        if self.cache_url:
            cache.source_uri = self.cache_url
        if self.geometry:
            cache.set_geometry_field(self.geometry)
        cache.save()
        cache.refresh_from_db()
        return cache

    def retrieve_cache(self) -> Cache:
        """Try to retrieve context from point.

        :returns: cache on None
        :rtype: cache or None
        """
        caches = Cache.objects.filter(csr=self.get_csr())
        for cache in caches:
            if cache.geometry and cache.geometry.contains(self.point):
                current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
                is_expired = current_time > cache.expired_time
                if is_expired:
                    cache.delete()
                    break
                else:
                    return cache

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
            LOGGER.error(
                f"'{self.csr_key}' url failed: {self.cache_url} with: {e}"
            )
            return None

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
