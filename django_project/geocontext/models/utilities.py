from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import logging
import pytz
import requests
import threading
from xml.dom import minidom
import xml.etree.ElementTree as ET

from django.contrib.gis.gdal.error import GDALException, SRSException
from django.contrib.gis.geos import GEOSGeometry, Point
from django.http import QueryDict

from geocontext.models.csr import CSR
from geocontext.models.cache import Cache
from geocontext.utilities import (
    convert_coordinate,
    dms_dd,
    get_bbox,
    round_point,
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
        """Load object. Transform user query to CSR geometry.

        Init method is not threadsafe so should be done before async logic

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
                    raise ValueError(f"Coord parse for {self.csr_key} failed: {coord}.")
            setattr(self, coord_attr_name, coord_dd)

        # Parse srid and create point in crs srid
        try:
            self.srid_in = int(self.srid_in)
            self.point = Point(self.x, self.y, srid=self.srid_in)
        except ValueError:
            raise ValueError(f"SRID: '{self.srid_in}' not valid")

        # TODO Round smartly using base data raster resolution
        # if self.query_type == ServiceDefinitions.WMS:
        #     if self.resolution:
        #         Calculate decimals depending on base resolution
        #         decimals = (1m = 5, 10m = 4, 100m = 3, 1000m = 2, 10000m = 1)

        # Round before converting as queries default 4326 - less conversions needed
        self.point = round_point(self.point, decimals=4)

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

    def request_content(self, url: str) -> requests:
        """Get request content from url in request session

        :param url: Url
        :type url: str

        :return: URL to do query.
        :rtype: unicode
        """
        session = get_session()
        with session.get(url) as response:
            if response.status_code == 200:
                return response.content

    def fetch_wms(self):
        """Fetch WMS value
        """
        parameters = {
            "SERVICE": self.query_type,
            "LAYERS": self.layer_typename,
            "QUERY_LAYERS": self.layer_typename,
            "BBOX": get_bbox(self.point),
            "WIDTH": 101,
            "HEIGHT": 101,
            'FORMAT': 'image/png',
            "INFO_FORMAT": 'application/json',
            "FEATURE_COUNT": 50
        }
        if self.service_version in ['1.0.0', '1.1.0']:
            parameters['WMTVER'] = self.service_version
            parameters['REQUEST'] = 'feature_info'
            parameters['SRS'] = 'EPSG:' + str(self.point.srid)
            parameters['X'] = 50
            parameters['Y'] = 50
        else:
            parameters['VERSION'] = self.service_version
            parameters['REQUEST'] = 'GetFeatureInfo'
            parameters['CRS'] = 'EPSG:' + str(self.point.srid)
            parameters['I'] = 50
            parameters['j'] = 50

        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            self.cache_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.cache_url = f'{self.url}?{query_dict.urlencode()}'

        getmap_content = self.request_content(self.cache_url)
        self.value = getmap_content["Features"][0][self.result_regex]

    def fetch_wfs(self):
        """Fetch WFS value - use intersect if polygon type else buffer
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

        describe_content = self.request_content(self.cache_url)
        geo_name, geo_type = self.parse_geometry_xml(describe_content)

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
            content = self.request_content(self.cache_url)

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
            content = self.request_content(self.cache_url)

        xmldoc = minidom.parseString(content)
        value_dom = xmldoc.getElementsByTagName(self.result_regex)[0]
        self.value = value_dom.childNodes[0].nodeValue

        # Add new geometry only if found - otherwise keep query point in cache
        new_geometry = self.parse_geometry_gml(content, self.layer_typename)
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
        content = self.request_content(self.cache_url)
        json_document = json.loads(content)
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
        content = self.request_content(self.cache_url)
        json_document = json.loads(content)
        self.value = json_document['geonames'][0][self.result_regex]

    def parse_geometry_xml(self, content: str) -> tuple:
        """Find geometry in xml string

        :param content: xml content
        :type content: str
        :return: geometry name and geometry type
        :rtype: tuple
        """
        content_parsed = ET.fromstring(content)
        version = None
        try:
            content_parsed.tag.split('}')[1]
            version = content_parsed.tag.split('}')[0] + '}'
        except IndexError:
            pass
        geometry_name, geometry_type = None, None
        try:
            complex_type = content_parsed.find(
                self.tag_with_version('complexType', version))
            complex_content = complex_type.find(
                self.tag_with_version('complexContent', version))
            extension = complex_content.find(
                self.tag_with_version('extension', version))
            sequences = extension.find(
                self.tag_with_version('sequence', version))
            for sequence in sequences:
                try:
                    if 'gml' in sequence.attrib['type']:
                        geometry_name = sequence.attrib['name']
                        geometry_type = sequence.attrib['type'].replace(
                            'gml:', '').replace('PropertyType', '')
                except KeyError:
                    continue
            pass
        except Exception as e:
            LOGGER.error(f"Could not find geometry in xml for {self.csr_key} with {e}")
            pass
        return geometry_name, geometry_type

    def parse_geometry_gml(self, gml_string: str, tag_name: str = 'qgs:geometry') \
            -> GEOSGeometry:
        """Parse geometry from gml document.

        :param gml_string: String that represent full gml document.
        :type gml_string: unicode

        :param tag_name: gml tag
        :type tag_name: str

        :returns: GEOGeometry from the gml document, the first one if there are
            more than one.
        :rtype: GEOSGeometry
        """
        try:
            xmldoc = minidom.parseString(gml_string)
        except Exception as e:
            LOGGER.error(f"Could not parse GML string for: {self.csr_key} with {e}")
            return None
        try:
            if tag_name == 'qgs:geometry':
                geometry_dom = xmldoc.getElementsByTagName(tag_name)[0]
                geometry_gml_dom = geometry_dom.childNodes[1]
                return GEOSGeometry.from_gml(geometry_gml_dom.toxml())
            else:
                tag_name = tag_name.split(':')[0] + ':' + 'geom'
                geometry_dom = xmldoc.getElementsByTagName(tag_name)[0]
                geometry_gml_dom = geometry_dom.childNodes[0]
                return GEOSGeometry.from_gml(geometry_gml_dom.toxml())

        except IndexError:
            LOGGER.error(f"No geometry found for: {self.csr_key}")
            return None
        except GDALException:
            LOGGER.error(f"GDAL error for: {self.csr_key}")
            return None

    def tag_with_version(self, tag: str, version: str) -> str:
        """ Replace version in tag

        :return: tag
        :rtype: str
        """
        if version:
            return version + tag
        return tag
