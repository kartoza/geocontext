from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import pytz
import requests
import threading

from owslib.wms import WebMapService
from xml.dom import minidom
from django.contrib.gis.geos import Point
from django.http import QueryDict

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


def thread_retrieve_external(util_arg_list):
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


def retrieve_external_csr(util_arg):
    """Fetch data and loads into CSRUtils instance
    using threadlocal request session.

    :param namedtuple: (group_key, csr_util)
    :type util_arg: namedtuple(int, CSRUtils)

    :return: (group_key and CSRUtils)
    :rtype: namedtuple or None
    """
    if util_arg.csr_util.retrieve_value():
        return util_arg
    else:
        return None


def get_session():
    """Get thread local request session"""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


class CSRUtils():
    """Mock context service registry model object + utility methods.
    Threadsafe - only __init__, get_ & create_cache
    access DB but does not store any connection/querysets.
    """
    def __init__(self, csr_key, x, y, srid=4326):
        """Generalized coordinate and load mock service registry.

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
        self.query_srid = srid
        self.generalize_point()
        self.geometry = self.point

    def get_csr(self):
        """Returns context service registry instance

        :raises KeyError: If registry not found

        :return: context service registry
        :rtype: CSR
        """
        try:
            return CSR.objects.get(key=self.csr_key)
        except CSR.DoesNotExist:
            raise KeyError('Service Registry not Found for'
                           f'{self.csr_key}')

    def generalize_point(self):
        """Generalize a point to to registry format.

        Converts degree, minute, second to decimal degree.
        Converts to SRID of the context registry
        Removes extreme precision to improve point cache hits.
        Default precision for is 4 decimals (~10m)

        :return: point
        :rtype: Point
        """
        # Parse DMS
        parsed = False
        dms_chars = ['°', "'", '"', 'N', 'S', 'E', 'W', 'n', 's', 'e', 'w']
        for coord in [self.x, self.y]:
            for dms_char in dms_chars:
                if dms_char in coord:
                    degrees, minutes, seconds = parse_dms(coord)
                    coord = dms_dd(degrees, minutes, seconds)
                    parsed = True
                    break

        # Value not DMS - assume DD and convert to float
        if not parsed:
            try:
                self.x = float(self.x)
                self.y = float(self.y)
            except ValueError:
                raise ValueError('Could not convert x/y to float')

        # Convert or set coordinate
        if self.query_srid != self.srid:
            point = Point(*convert_coordinate(self.x, self.y, self.query_srid, self.srid),
                          srid=self.srid
                          )
        else:
            point = Point(self.x, self.y, srid=self.srid)

        # Set precision after projection
        decimals = 4
        x_round = Decimal(point.x).quantize(Decimal('0.' + '0' * decimals))
        y_round = Decimal(point.y).quantize(Decimal('0.' + '0' * decimals))
        self.point = Point(float(x_round), float(y_round), srid=self.srid)

    def create_cache(self):
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

    def retrieve_cache(self):
        """Try to retrieve context from point.

        :returns: cache on None
        :rtype: cache or None
        """
        caches = Cache.objects.filter(csr=self.get_csr())
        for cache in caches:
            if cache.geometry:
                if cache.geometry.contains(self.point):
                    current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
                    is_expired = current_time > cache.expired_time
                    if not is_expired:
                        return cache
                    else:
                        cache.delete()
                        break

    def retrieve_value(self):
        """Load context value.

        :returns: success
        :rtype: bool
        """
        if self.query_type == ServiceDefinitions.WMS:
            try:
                wms = WebMapService(self.url, self.service_version)
                response = wms.getfeatureinfo(
                    layers=[self.layer_typename],
                    bbox=get_bbox(self.point.x, self.point.y),
                    size=[101, 101],
                    xy=[50, 50],
                    srs='EPSG:' + str(self.point.srid),
                    info_format='application/vnd.ogc.gml'
                )
                wms_content = response.read()
                self.value = self.parse_request_value(wms_content)
                self.cache_url = response.geturl()
            except NotImplementedError as e:
                self.value = e
            return True

        if self.query_type in [ServiceDefinitions.ARCREST, ServiceDefinitions.PLACENAME]:
            self.cache_url = self.box_query_url()
            build_content = self.request_content()
            if build_content is not None:
                self.value = self.parse_request_value(build_content)
                if self.value is not None:
                    return True

        else:
            self.cache_url = self.describe_query_url()
            describe_content = self.request_content()
            if describe_content is None:
                return False

            geo_name, geo_type = find_geometry_in_xml(describe_content)

            # Try quick polygon intersection query
            if 'Polygon' in geo_type:
                self.cache_url = self.intersect_query_url(geo_name)
                gml_string = self.request_content()
                if gml_string is not None:
                    self.value = self.parse_request_value(gml_string)
                    if self.value is not None:
                        self.fetch_geometry(gml_string)
                    return True

            # Else try boundingbox
            else:
                self.cache_url = self.box_query_url()
                gml_string = self.request_content()
                if gml_string is not None:
                    self.value = self.parse_request_value(gml_string)
                    if self.value is not None:
                        self.fetch_geometry(gml_string)
                    return True

        self.value = "error"
        return False

    def request_content(self, retries=0):
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
                f"'{self.service_registry_key}' url failed: {self.cache_url} with: {e}"
            )
            return None

    def fetch_geometry(self, gml_string):
        """Get request geometry from gml string

        :param gml_string: String that represent full gml document.
        :type gml_string: unicode

        :return: URL to do query.
        :rtype: unicode
        """
        geom = parse_gml_geometry(gml_string, self.layer_typename)
        if geom is not None:
            if not geom.srid:
                geom.srid = self.srid
            self.geometry = geom

    def parse_request_value(self, request_content):
        """Parse request value from request content.

        :param request_content: String that represent content of a request.
        :type request_content: unicode

        :returns: The value of the result_regex in the request_content.
        :rtype: unicode
        """
        if self.query_type in [ServiceDefinitions.WFS, ServiceDefinitions.WMS]:
            xmldoc = minidom.parseString(request_content)
            try:
                value_dom = xmldoc.getElementsByTagName(self.result_regex)[0]
                return value_dom.childNodes[0].nodeValue
            except IndexError:
                pass
            if self.result_regex == 'gml:name':
                try:
                    value_dom = xmldoc.getElementsByTagName('gml:description')[0]
                    return value_dom.childNodes[0].nodeValue
                except IndexError:
                    return None
        # For the ArcREST standard we parse JSON (Above parsed from CSV)
        elif self.query_type == ServiceDefinitions.ARCREST:
            json_document = json.loads(request_content)
            try:
                json_value = json_document['results'][0][self.result_regex]
                return json_value
            except IndexError:
                return None
        # PlaceName also parsed from JSONS but document structure differs.
        elif self.query_type == ServiceDefinitions.PLACENAME:
            json_document = json.loads(request_content)
            try:
                json_value = json_document['geonames'][0][self.result_regex]
                return json_value
            except IndexError:
                return None

    def box_query_url(self):
        """Build query with bounding box.

        :return: URL to do query.
        :rtype: unicode
        """
        url = None
        bbox = get_bbox(self.point.x, self.point.y)
        bbox_string = ','.join([str(i) for i in bbox])

        if self.query_type == ServiceDefinitions.WFS:
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
                url = f'{self.url}&{query_dict.urlencode()}'
            else:
                url = f'{self.url}?{query_dict.urlencode()}'
            if ':' not in self.layer_typename:
                url += f'&SRSNAME={self.point.srid}'
            url += '&BBOX=' + bbox_string

        elif self.query_type == ServiceDefinitions.ARCREST:
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
                url = f'{self.url}&{query_dict.urlencode()}'
            else:
                url = f'{self.url}/identify?{query_dict.urlencode()}'
                url += f'&mapExtent={bbox_string}'

        elif self.query_type == ServiceDefinitions.PLACENAME:
            parameters = {
                'lat': str(self.point.y),
                'lng': str(self.point.x),
                'username': str(self.api_key),
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                url = f'{self.url}&{query_dict.urlencode()}'
            else:
                url = f'{self.url}?{query_dict.urlencode()}'
        return url

    def describe_query_url(self):
        """Describe query based on the model and the parameter.

        :return: URL to do query.
        :rtype: unicode
        """
        describe_url = None
        if self.query_type == ServiceDefinitions.WFS:
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'DescribeFeatureType',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                describe_url = f'{self.url}&{query_dict.urlencode()}'
            else:
                describe_url = f'{self.url}?{query_dict.urlencode()}'
        return describe_url

    def intersect_query_url(self, geom_name):
        """Filter query based on the model and the parameter.

        :return: URL to do query.
        :rtype: unicode
        """
        filter_url = None
        attribute_name = (self.result_regex[4:])
        layer_filter = ('<Filter xmlns="http://www.opengis.net/ogc" '
                        'xmlns:gml="http://www.opengis.net/gml"> '
                        f'<Intersects><PropertyName>{geom_name}</PropertyName>'
                        f'<gml:Point srsName="EPSG:{self.point.srid}">'
                        f'<gml:coordinates>{self.point.x},{self.point.y}'
                        '</gml:coordinates></gml:Point></Intersects></Filter>'
                        )

        if self.query_type == ServiceDefinitions.WFS:
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'FILTER': layer_filter,
                'PROPERTYNAME': f'({attribute_name})',
                'MAXFEATURES': 1,
                'OUTPUTFORMAT': 'GML3',
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                filter_url = f'{self.url}&{query_dict.urlencode()}'
            else:
                filter_url = f'{self.url}?{query_dict.urlencode()}'
            if ':' not in self.layer_typename:
                filter_url += f'&SRSNAME={self.point.srid}'
        return filter_url
