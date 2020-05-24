from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal
import fnmatch
import json
import logging
import pytz
import threading
import requests

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


def thread_retrieve_external(registry_utils):
    new_result_list = []
    with ThreadPoolExecutor() as executor:
        for result in executor.map(retrieve_from_registry_util, registry_utils):
            new_result_list.append(result)
    return new_result_list


def retrieve_from_registry_util(registry_util):
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    registry_util[1].retrieve_context_value(thread_local.session)
    return (registry_util[0], registry_util[1])


class ContextServiceRegistryUtils():
    """Utility class for context registry model
    only __init__, get&create_context_cache access DB 
    but does not store any direct data.
    """

    def __init__(self, service_registry_key, x, y, srid=4326):
        self.service_registry_key = service_registry_key
        service_registry = self.get_service_registry()
        self.query_type = service_registry.query_type
        self.service_version = service_registry.service_version
        self.layer_typename = service_registry.layer_typename
        self.result_regex = service_registry.result_regex
        self.url = service_registry.url
        self.api_key = service_registry.api_key
        service_registry = None
        self.point = self.generalize_point(x, y, srid)
        self.geometry = self.point
        self.new_url = None
        self.parsed_value = None

    def get_service_registry(self):
        try:
            return ContextServiceRegistry.objects.get(key=self.service_registry_key)
        except ContextServiceRegistry.DoesNotExist:
            raise KeyError(f'Service Registry not Found for {self.service_registry_key}')

    def generalize_point(self, x, y, srid):
        """Generalize a point to standard srid grid depending on data source type.
        Cache does not need to contain data at higher resolution than
        native_resolution. This is done after projection but before quering
        cache/web service.

        Default precision for non WFS is 4 decimals (~10m)

        :param point: Point
        :type point: GEOS point
        :param service_registry: Context service registry object
        :type service_registry: model object
        :return: point
        :rtype: Point
        """
        if srid != 4326:
            point = Point(*convert_coordinate(x, y, srid, 4326), srid=4326)
        else:
            point = Point(x, y, srid=4326)

        if self.query_type != ServiceDefinitions.WFS:
            decimals = 4
            x_round = Decimal(point.x).quantize(Decimal('0.' + '0' * decimals))
            y_round = Decimal(point.y).quantize(Decimal('0.' + '0' * decimals))
            point = Point(float(x_round), float(y_round), srid=4326)
        return point

    def retrieve_context_cache(self):
        """Retrieve context from point x, y.

        :returns: context_cache
        :rtype: context_cache or None
        """
        caches = ContextCache.objects.filter(service_registry=self.get_service_registry())

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

    def retrieve_context_value(self, session):
        """Retrieve context from a location.
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
                content = response.read()
                self.parsed_value = self.parse_request_value(content)
                self.new_url = response.geturl()
            except NotImplementedError as e:
                self.parsed_value = e
        elif self.query_type in (
                ServiceDefinitions.ARCREST,
                ServiceDefinitions.PLACENAME):
            self.new_url = self.build_query_url()
            request = session.get(self.new_url)
            if request.status_code == 200:
                content = request.content
                self.parsed_value = self.parse_request_value(content)
        else:
            parameter_url = self.describe_query_url()
            geo_name, geo_type = find_geometry_in_xml(parameter_url)
            if None in [geo_name, geo_type]:
                return None
            if fnmatch.fnmatch(geo_type, '*Polygon*'):
                self.new_url = self.filter_query_url()
                request = session.get(self.new_url)
                if request.status_code == 200:
                    content = request.content
                    self.parsed_value = self.parse_request_value(content)
            else:
                self.new_url = self.build_query_url()
                request = session.get(self.new_url)
                if request.status_code == 200:
                    content = request.content
                    if ':' in self.layer_typename:
                        workspace = self.layer_typename.split(':')[0]
                        geometry = parse_gml_geometry(content, workspace)
                    elif self.query_type != ServiceDefinitions.PLACENAME:
                        geometry = parse_gml_geometry(content)
                    if not geometry:
                        return None
                    if not geometry.srid:
                        geometry.srid = self.point.srid
                    self.parsed_value = self.parse_request_value(content)
                else:
                    error_message = (
                        f'{self.new_url} url failed for CSR: {self.service_registry_key}.'
                        f'Got: {request.status_code} because of reasons: {request.reason}'
                    )
                    LOGGER.error(error_message)
                    self.parsed_value = None

    def create_context_cache(self):
        service_registry = self.get_service_registry()
        expired_time = (
            datetime.utcnow() + timedelta(seconds=service_registry.time_to_live)
        )
        expired_time = expired_time.replace(tzinfo=pytz.UTC)
        context_cache = ContextCache(
            service_registry=service_registry,
            name=service_registry.key,
            value=self.parsed_value,
            expired_time=expired_time
        )
        service_registry = None
        if self.new_url:
            context_cache.source_uri = self.new_url
        if self.geometry:
            context_cache.set_geometry_field(self.geometry)
        context_cache.save()
        context_cache.refresh_from_db()
        return context_cache

    def parse_request_value(self, request_content):
        """Parse request value from request content.

        :param request_content: String that represent content of a request.
        :type request_content: unicode

        :returns: The value of the result_regex in the request_content.
        :rtype: unicode
        """
        if self.query_type in [
            ServiceDefinitions.WFS, ServiceDefinitions.WMS]:
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

    def filter_query_url(self):
        """Filter query based on the model and the parameter.

        :return: URL to do query.
        :rtype: unicode
        """
        parameter_url = self.describe_query_url()
        geom_name, geom_type = find_geometry_in_xml(parameter_url)
        filter_url = None
        # construct bbox
        attribute_name = (self.result_regex[4:])
        layer_filter = ('<Filter xmlns="http://www.opengis.net/ogc" '
                        'xmlns:gml="http://www.opengis.net/gml"> '
                        f'<Intersects><PropertyName>{geom_name}</PropertyName>'
                        '<gml:Point srsName="EPSG:4326"> '
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
            # Only add SRSNAME when there is no workspace
            if ':' not in self.layer_typename:
                filter_url += f'&SRSNAME={self.point.srid}'
        return filter_url
