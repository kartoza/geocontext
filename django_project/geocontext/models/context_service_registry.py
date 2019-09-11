# coding=utf-8
"""Context Service Registry Model."""

import requests
import json
import logging
from datetime import datetime, timedelta
import pytz
import fnmatch
from xml.dom import minidom

from owslib.wms import WebMapService

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.http import QueryDict

from geocontext.utilities import (
    convert_coordinate, parse_gml_geometry, get_bbox, find_geometry_in_xml)
from geocontext.models.validators import key_validator

LOGGER = logging.getLogger(__name__)


class ContextServiceRegistry(models.Model):
    """Context Service Registry"""

    WFS = 'WFS'
    WCS = 'WCS'
    WMS = 'WMS'
    REST = 'REST'
    ARCREST = 'ArcREST'
    WIKIPEDIA = 'Wikipedia'
    PLACENAME = 'PlaceName'
    QUERY_TYPES = (
        (WFS, 'WFS'),
        (WCS, 'WCS'),
        (WMS, 'WMS'),
        (REST, 'REST'),
        (ARCREST, 'ArcREST'),
        (WIKIPEDIA, 'Wikipedia'),
        (PLACENAME, 'PlaceName'),
    )

    key = models.CharField(
        help_text=_('Key of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
        unique=True,
        validators=[key_validator],
    )

    name = models.CharField(
        help_text=_('Name of Context Service.'),
        blank=False,
        null=False,
        max_length=200,
    )

    description = models.CharField(
        help_text=_('Description of Context Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    url = models.CharField(
        help_text=_('URL of Context Service.'),
        blank=False,
        null=False,
        max_length=1000,
    )

    user = models.CharField(
        help_text=_('User name for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    password = models.CharField(
        help_text=_('Password for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=200,
    )

    api_key = models.CharField(
        help_text=_(
            'API key for accessing Context Service. For PlaceName queries '
            'this is your username.'),
        blank=True,
        null=True,
        max_length=200,
    )

    query_url = models.CharField(
        help_text=_('Query URL for accessing Context Service.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    query_type = models.CharField(
        help_text=_('Query type of the Context Service.'),
        blank=False,
        null=False,
        max_length=200,
        choices=QUERY_TYPES,
    )

    # I will try to use CharField first, if not I will use django-regex-field
    result_regex = models.CharField(
        help_text=_('Regex to retrieve the desired value.'),
        blank=False,
        null=False,
        max_length=200,
    )

    time_to_live = models.IntegerField(
        help_text=_(
            'Time to live of Context Service to be used in caching in '
            'seconds unit.'),
        blank=True,
        null=True,
        default=604800  # 7 days
    )

    srid = models.IntegerField(
        help_text=_('The Spatial Reference ID of the service registry.'),
        blank=True,
        null=True,
        default=4326
    )

    layer_typename = models.CharField(
        help_text=_('Layer type name to get the context.'),
        blank=False,
        null=False,
        max_length=200,
    )

    service_version = models.CharField(
        help_text=_('Version of the service (e.g. WMS 1.1.0, WFS 2.0.0).'),
        blank=False,
        null=False,
        max_length=200,
    )

    provenance = models.CharField(
        help_text=_('The origin or source of the Context Service Registry.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    notes = models.TextField(
        help_text=_('Notes for the Context Service Registry.'),
        blank=True,
        null=True,
    )

    licensing = models.CharField(
        help_text=_('The licensing scheme for the Context Service Registry.'),
        blank=True,
        null=True,
        max_length=1000,
    )

    def __str__(self):
        return self.name

    def retrieve_context_value(self, x, y, srid=4326):
        """Retrieve context from a location.

        :param x: The value of x coordinate.
        :type x: float

        :param y: The value of y coordinate.
        :type y: float

        :param srid: The srid of the coordinate.
        :type srid: int

        :
        """
        url = None
        geometry = None
        if self.query_type == ContextServiceRegistry.WMS:
            try:
                wms = WebMapService(self.url, self.service_version)
                response = wms.getfeatureinfo(
                    layers=[self.layer_typename],
                    bbox=get_bbox(x, y),
                    size=[101, 101],
                    xy=[50, 50],
                    srs='EPSG:' + str(srid),
                    info_format='application/vnd.ogc.gml'
                )
                content = response.read()
                parsed_value = self.parse_request_value(content)
                # No geometry and url for WMS
                geometry = None
                url = response.geturl()
            except NotImplementedError as e:
                parsed_value = e

        elif self.query_type in (
                ContextServiceRegistry.ARCREST,
                ContextServiceRegistry.PLACENAME):
            url = self.build_query_url(x, y, srid)
            request = requests.get(url)
            if request.status_code == 200:
                content = request.content
                parsed_value = self.parse_request_value(content)

        else:
            parameter_url = self.describe_query_url()
            geo_name, geo_type = find_geometry_in_xml(parameter_url)
            if fnmatch.fnmatch(geo_type, '*Polygon*'):
                url = self.filter_query_url(x, y, srid)
                request = requests.get(url)
                if request.status_code == 200:
                    content = request.content
                    parsed_value = self.parse_request_value(content)

            else:

                url = self.build_query_url(x, y, srid)
                request = requests.get(url)
                if request.status_code == 200:
                    content = request.content
                    if ':' in self.layer_typename:
                        workspace = self.layer_typename.split(':')[0]
                        geometry = parse_gml_geometry(content, workspace)
                    elif self.query_type != ContextServiceRegistry.PLACENAME:
                        geometry = parse_gml_geometry(content)
                    if not geometry:
                        return None
                    if not geometry.srid:
                        geometry.srid = self.srid
                    parsed_value = self.parse_request_value(content)
                else:
                    error_message = (
                        'Failed to request to {url} for CSR {key} got '
                        '{status_code} because of reasons'.format(
                            url=url,
                            key=self.key,
                            status_code=request.status_code,
                            reason=request.reason,
                        ))
                    LOGGER.error(error_message)
                    parsed_value = None

        # Create cache here.
        from geocontext.models.context_cache import ContextCache
        expired_time = datetime.utcnow() + timedelta(seconds=self.time_to_live)
        # Set timezone to UTC
        expired_time = expired_time.replace(tzinfo=pytz.UTC)
        context_cache = ContextCache(
            service_registry=self,
            name=self.key,
            value=parsed_value,
            expired_time=expired_time
        )

        if url:
            context_cache.source_uri = url

        if geometry:
            context_cache.set_geometry_field(geometry)
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
            ContextServiceRegistry.WFS, ContextServiceRegistry.WMS]:
            xmldoc = minidom.parseString(request_content)
            try:
                value_dom = xmldoc.getElementsByTagName(self.result_regex)[0]
                return value_dom.childNodes[0].nodeValue
            except IndexError:
                return None
        # For the ArcREST standard we parse JSON (Above parsed from CSV)
        elif self.query_type == ContextServiceRegistry.ARCREST:
            json_document = json.loads(request_content)
            try:
                json_value = json_document['results'][0][self.result_regex]
                return json_value
            except IndexError:
                return None
        # PlaceName also parsed from JSONS but document structure differs.
        elif self.query_type == ContextServiceRegistry.PLACENAME:
            json_document = json.loads(request_content)
            try:
                json_value = json_document['geonames'][0][self.result_regex]
                return json_value
            except IndexError:
                return None

    def build_query_url(self, x, y, srid=4326):
        """Build query based on the model and the parameter.

        :param x: The value of x coordinate.
        :type x: float

        :param y: The value of y coordinate.
        :type y: float

        :param srid: The srid of the coordinate.
        :type srid: int

        :return: URL to do query.
        :rtype: unicode
        """
        url = None
        # construct bbox
        if srid != self.srid:
            x, y = convert_coordinate(x, y, srid, self.srid)
        bbox = get_bbox(x, y)
        bbox_string = ','.join([str(i) for i in bbox])
        if self.query_type == ContextServiceRegistry.WFS:
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
                url = '{current_url}&{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            else:
                url = '{current_url}?{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            # Only add SRSNAME when there is no workspace
            if ':' not in self.layer_typename:
                url += '&SRSNAME=%s' % self.srid
            url += '&BBOX=' + bbox_string
        # ARCRest URL Construction:
        elif self.query_type == ContextServiceRegistry.ARCREST:
            parameters = {
                'f': 'json',
                'geometryType': 'esriGeometryPoint',
                'geometry': '{{x: {x_coordinate}, y: {y_coordinate} }}'.format(
                    x_coordinate=x,
                    y_coordinate=y,
                ),
                # Layers are recalled with all:<number> in QGIS' call
                'layers': self.layer_typename,
                'imageDisplay': '581,461,96',
                'tolerance': '10',
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                url = '{current_url}&{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            else:
                url = '{current_url}/identify?{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode())
                url += '&mapExtent={bbox_string}'.format(
                    current_url=self.url,
                    bbox_string=bbox_string
                )
        elif self.query_type == ContextServiceRegistry.PLACENAME:
            parameters = {
                # http://api.geonames.org/findNearbyPlaceNameJSON?
                # lat=-32.32&lng=19.14&username=christiaanvdm
                'lat': str(y),
                'lng': str(x),
                'username': str(self.api_key),
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                url = '{current_url}&{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            else:
                url = '{current_url}?{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode())
        return url

    def describe_query_url(self):
        """Build query based on the model and the parameter.

        :param x: The value of x coordinate.
        :type x: float

        :param y: The value of y coordinate.
        :type y: float

        :param srid: The srid of the coordinate.
        :type srid: int

        :return: URL to do query.
        :rtype: unicode
        """
        describe_url = None
        if self.query_type == ContextServiceRegistry.WFS:
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'DescribeFeatureType',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                describe_url = '{current_url}&{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            else:
                describe_url = '{current_url}?{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
        return describe_url

    def filter_query_url(self, x, y, srid=4326):
        """Build query based on the model and the parameter.

        :param x: The value of x coordinate.
        :type x: float

        :param y: The value of y coordinate.
        :type y: float

        :param srid: The srid of the coordinate.
        :type srid: int

        :return: URL to do query.
        :rtype: unicode
        """
        parameter_url = self.describe_query_url()
        geom_name, geom_type = find_geometry_in_xml(parameter_url)
        filter_url = None
        # construct bbox
        attribute_name = (self.result_regex[4:])
        layer_filter = ''' <Filter xmlns="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml"> \
                        <Intersects><PropertyName>%s</PropertyName><gml:Point srsName="EPSG:4326"> \
                        <gml:coordinates>%s,%s</gml:coordinates></gml:Point></Intersects></Filter>''' % (
            geom_name, x, y)

        if self.query_type == ContextServiceRegistry.WFS:
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'FILTER': layer_filter,
                'PROPERTYNAME': '(%s)' % attribute_name,
                'MAXFEATURES': 1,
                'OUTPUTFORMAT': 'GML3',
            }
            query_dict = QueryDict('', mutable=True)
            query_dict.update(parameters)
            if '?' in self.url:
                filter_url = '{current_url}&{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            else:
                filter_url = '{current_url}?{urlencoded_parameters}'.format(
                    current_url=self.url,
                    urlencoded_parameters=query_dict.urlencode(),
                )
            # Only add SRSNAME when there is no workspace
            if ':' not in self.layer_typename:
                filter_url += '&SRSNAME=%s' % self.srid

        return filter_url
