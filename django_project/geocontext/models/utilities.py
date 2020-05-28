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

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_cache import ContextCache
from geocontext.utilities import (
    convert_coordinate,
    find_geometry_in_xml,
    get_bbox,
    parse_gml_geometry,
    ServiceDefinitions,
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
    if util_arg.csr_util.retrieve_context_value():
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
    Threadsafe - only __init__, get_ & create_context_cache
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
        self.service_registry_key = csr_key
        service_registry = self.get_service_registry()
        self.query_type = service_registry.query_type
        self.service_version = service_registry.service_version
        self.layer_typename = service_registry.layer_typename
        self.result_regex = service_registry.result_regex
        self.api_key = service_registry.api_key
        self.url = service_registry.url
        self.srid = service_registry.srid
        self.cache_url = None
        self.value = None
        service_registry = None

        # Geometry defaults to generalized point - for basic cache hits.
        self.x = x
        self.y = y       
        self.query_srid = srid
        self.generalize_point()
        self.geometry = self.point

    def get_service_registry(self):
        """Returns context service registry instance

        :raises KeyError: If registry not found

        :return: context service registry
        :rtype: ContextServiceRegistry
        """
        try:
            return ContextServiceRegistry.objects.get(
                key=self.service_registry_key)
        except ContextServiceRegistry.DoesNotExist:
            raise KeyError('Service Registry not Found for'
                           f'{self.service_registry_key}')

    def generalize_point(self):
        """Generalize a point to standard srid grid depending on data source type.
        Cache does not need to contain data at higher resolution than
        native_resolution.

        Default precision for is 4 decimals (~10m)

        :return: point
        :rtype: Point
        """
        
        if self.query_srid != self.srid:
            point = Point(
                *convert_coordinate(self.x, self.y, self.query_srid, self.srid),
                srid=self.srid
            )
        else:
            point = Point(self.x, self.y, srid=self.srid)

        decimals = 4
        x_round = Decimal(point.x).quantize(Decimal('0.' + '0' * decimals))
        y_round = Decimal(point.y).quantize(Decimal('0.' + '0' * decimals))
        self.point = Point(float(x_round), float(y_round), srid=self.srid)

    def retrieve_context_cache(self):
        """Retrieve context from point.

        :returns: context_cache on None
        :rtype: context_cache or None
        """
        caches = ContextCache.objects.filter(
            service_registry=self.get_service_registry())

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

    def retrieve_context_value(self):
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
            build_url = self.build_query_url()
            build_content = self.request_content(build_url)
            if build_content is not None:
                self.value = self.parse_request_value(build_content)

        else:
            describe_url = self.describe_query_url()
            describe_content = self.request_content(describe_url)
            if describe_content is None:
                return False

            geo_name, geo_type = find_geometry_in_xml(describe_content)

            filter_url = self.filter_query_url(geo_name)
            filter_content = self.request_content(filter_url)
            if filter_content is not None:
                self.value = self.parse_request_value(filter_content)

            if self.query_type == ServiceDefinitions.PLACENAME:
                return True

            build_url = self.build_query_url()
            build_content = self.request_content(build_url)        
            if build_content is not None:
                geometry = parse_gml_geometry(build_content, self.layer_typename)
                if geometry is not None:
                    geometry.srid = self.srid if not geometry.srid else geometry.srid
                    self.geometry = geometry

        self.cache_url = build_url
        return True

    def request_content(self, url, retries=0):
        """Get request content from url in request session

        :param url: URL to do query.
        :type url: unicode

        :return: URL to do query.
        :rtype: unicode
        """
        session = get_session()
        try:
            with session.get(url) as response:
                if response.status_code == 200:
                    return response.content
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"'{self.service_registry_key}' url failed: {url} with: {e}")
            return None

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

    def build_query_url(self):
        """Build query based on the model and the parameter.

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

    def filter_query_url(self, geom_name):
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

    def create_context_cache(self):
        """Add context value to cache

        :return: Context cache instance
        :rtype: ContextCache
        """
        service_registry = self.get_service_registry()
        expired_time = (datetime.utcnow() + timedelta(
                        seconds=service_registry.time_to_live))
        expired_time = expired_time.replace(tzinfo=pytz.UTC)
        context_cache = ContextCache(
            service_registry=service_registry,
            name=service_registry.key,
            value=self.value,
            expired_time=expired_time
        )
        service_registry = None
        if self.cache_url:
            context_cache.source_uri = self.cache_url
        if self.geometry:
            context_cache.set_geometry_field(self.geometry)
        context_cache.save()
        context_cache.refresh_from_db()
        return context_cache
