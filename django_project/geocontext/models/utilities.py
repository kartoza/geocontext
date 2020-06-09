import aiohttp
from arcgis2geojson import arcgis2geojson
import asyncio
from collections import namedtuple
from datetime import datetime, timedelta
import json
import logging
import pytz

from asgiref.sync import async_to_sync
from django.contrib.gis.gdal.error import SRSException
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import Distance
from django.http import QueryDict

from geocontext.models.service import Service
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


def create_cache(service_util) -> Cache:
    """Add context value to cache

    :param service_util: ServiceUtils instance
    :type service_util: ServiceUtils

    :return: Context cache instance
    :rtype: Cache
    """
    service = Service.objects.get(key=service_util.key)
    expired_time = (datetime.utcnow() + timedelta(seconds=service.cache_duration))
    expired_time = expired_time.replace(tzinfo=pytz.UTC)
    cache = Cache(
        service=service,
        name=service.key,
        value=service_util.value,
        expired_time=expired_time
    )
    if service_util.cache_url:
        cache.source_uri = service_util.cache_url
    if service_util.geometry:
        if service_util.geometry.hasz:
            cache.geometry = service_util.geometry
        else:
            cache.geometry = convert_2d_to_3d(service_util.geometry)
    cache.save()
    cache.refresh_from_db()
    return cache


def retrieve_cache(service_util) -> Cache:
    """Try to retrieve service cache from query point input.
    Filters for search distance and expiry date.

    :param service_util: ServiceUtils instance
    :type service_util: ServiceUtils

    :returns: cache on None
    :rtype: cache or None
    """
    current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
    service = Service.objects.get(key=service_util.key)
    caches = Cache.objects.filter(
        service=service,
        expired_time__lte=current_time,
        geometry__distance_lte=(
            service_util.geometry,
            Distance(m=service_util.search_dist))
    )
    return caches.first()


# Data object to index service utils with associated groups for serializer utils
UtilArg = namedtuple('UtilArgs', ['group_key', 'service_util'])


@async_to_sync
async def async_retrieve_service(util_arg_list: list) -> list:
    """Fetch data and loads into ServiceUtils instance using async session.

    :param namedtuple: (group_key, service_util)
    :type util_arg: namedtuple(str, ServiceUtils)

    :return: (group_key and ServiceUtils)
    :rtype: namedtuple or None
    """
    conn = aiohttp.TCPConnector(limit=100)
    timeout = aiohttp.ClientTimeout(total=60, connect=2)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = []
        for util_arg in util_arg_list:
            util_arg.service_util.session = session
            task = asyncio.ensure_future(async_worker(util_arg))
            tasks.append(task)
        new_util_arg_list = await asyncio.gather(*tasks)
        return new_util_arg_list


async def async_worker(util_arg: namedtuple) -> namedtuple:
    """Fetch data and loads into ServiceUtils instance.

    :param namedtuple: (group_key, service_util)
    :type util_arg: namedtuple(str, ServiceUtils)

    :return: (group_key and ServiceUtils)
    :rtype: namedtuple or None
    """
    await util_arg.service_util.retrieve_value()
    return util_arg


class ServiceUtils():
    """Async context service model mock object + utility methods.
    Init method calls ORM / blocking functions so should be done before async logic
    """
    def __init__(self, service_key: str, x: float, y: float,
                 srid_in: int = 4326, dist: float = 10.0):
        """Load object. Prepare geometry. This __init__ is async blocking.

        :param service_key: service_key
        :type service_key: str

        :param x: (longitude)
        :type x: float

        :param y: Y (latitude)
        :type y: float

        :param srid: SRID (default=4326).
        :type srid: int

        :param dist: Search distance query overide service (default=10.0).
        :type dist: int
        """
        # Unpack model into attributes
        service_dict = Service.objects.filter(key=service_key).values().first()
        for key, val in service_dict.items():
            setattr(self, key, val)

        # Add Cache model params
        self.cache_url = None
        self.value = None
        self.session = None

        # Search distance query overrides service in model - else default 10m
        if dist != 10.0:
            self.search_dist = dist
        elif self.search_dist is None:
            self.search_dist = 10

        # Parse Coordinate try DD / otherwise DMS
        coords = {'x': x, 'y': y}
        for coord, val in coords.items():
            try:
                coords[coord] = float(val)
            except ValueError:
                try:
                    degrees, minutes, seconds = parse_dms(val)
                    coords[coord] = dms_dd(degrees, minutes, seconds)
                except ValueError:
                    raise ValueError(
                        f"Coord '{coords[coord]}' parse failed: {self.key}")

        # Parse srid and create point in crs srid
        try:
            srid_in = int(srid_in)
            self.geometry = Point(coords['x'], coords['y'], srid=srid_in)
        except ValueError:
            raise ValueError(f"SRID: '{srid_in}' not valid")

        # Default geometry is point
        if srid_in != self.srid:
            try:
                self.geometry = convert_coordinate(self.geometry, self.srid)
            except SRSException:
                raise ValueError(f"SRID '{srid_in}' not valid: {self.key}")

        # Calculate bbox
        self.bbox = get_bbox(self.geometry)

    async def retrieve_value(self) -> bool:
        """Load context value.
        All exceptions / logging / nulls for all services handled here.
        """
        try:
            if self.query_type == ServiceDefinitions.WMS:
                await self.fetch_wms()
            elif self.query_type == ServiceDefinitions.WFS:
                await self.fetch_wfs()
            elif self.query_type == ServiceDefinitions.ARCREST:
                await self.fetch_arcrest()
            elif self.query_type == ServiceDefinitions.PLACENAME:
                await self.fetch_placename()
            else:
                LOGGER.error(f"'{self.query_type}' not implimented: {self.key}")
                self.value = None
        except IndexError:
            LOGGER.error(f"{self.cache_url} No features found for: {self.key}")
            self.value = None
        except Exception as e:
            LOGGER.error(f"{self.cache_url} failed for: {self.key} with: {e}")
            self.value = None

    async def fetch_wms(self):
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
            parameters['SRS'] = 'EPSG:' + str(self.geometry.srid)
            parameters['X'] = 5
            parameters['Y'] = 5
        else:
            parameters['REQUEST'] = 'GetFeatureInfo'
            parameters['CRS'] = 'EPSG:' + str(self.geometry.srid)
            parameters['I'] = 5
            parameters['j'] = 5

        json_response = await self.request_data(parameters)
        self.value = json_response["features"][0]["properties"][self.layer_name]

    async def fetch_wfs(self):
        """Fetch WFS value

        Try intersect else buffer with search distance.
        We don't do a describe feature request first as we can just try the
        the intersect and do a bbox if it fails - skipping an extra request.
        """
        layer_filter = (
            '<Filter xmlns="http://www.opengis.net/ogc" '
            'xmlns:gml="http://www.opengis.net/gml"> '
            f'<Intersects><PropertyName>geom</PropertyName>'
            f'<gml:Point srsName="EPSG:{self.geometry.srid}">'
            f'<gml:coordinates>{self.geometry.x},{self.geometry.y}'
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

        # TODO Axis order of 1.0.0 services not trusted -- see docs.geoserver.org
        if self.service_version in ['1.0.0']:
            pass
        else:
            pass

        json_response = await self.request_data(parameters)
        if len(json_response["features"]) > 0:
            self.value = json_response["features"][0]["properties"][self.layer_name]
        else:
            LOGGER.info(f"WFS intersect filter failed: {self.key} - attempt bbox")
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'OUTPUTFORMAT': 'application/json',
                'SRSNAME': f'EPSG:{self.geometry.srid}',
                'BBOX': self.bbox
            }

            json_response = await self.request_data(parameters)
            self.value = json_response["features"][0]["properties"][self.layer_name]
        await self.extract_geometry(json_response["features"][0]["geometry"])

    async def fetch_arcrest(self):
        """Fetch ArcRest value
        """
        parameters = {
            'f': 'json',
            'geometryType': 'esriGeometryPoint',
            'geometry': f'{{{{x: {self.geometry.x}, y: {self.geometry.y}}}}}',
            'layers': self.layer_name,
            'imageDisplay': '581,461,96',
            'tolerance': '10',
            'mapExtent': self.bbox
        }

        json_response = await self.request_data(parameters, query='identify?')
        self.value = json_response['results'][0][self.layer_name]
        await self.extract_geometry(json_response['results'][0]['geometry'], arc = True)

    async def fetch_placename(self):
        """Fetch Placename value
        """
        parameters = {
            'lat': str(self.geometry.y),
            'lng': str(self.geometry.x),
            'username': str(self.username),
        }

        json_response = await self.request_data(parameters)
        self.value = json_response['geonames'][0][self.layer_name]

    async def request_data(self, parameters: dict, query: str = "?") -> dict:
        """Encodes query URL from querydict and fetches json data with async session.

        :param parameters: parameters to urlencode
        :type parameters: dict

        :param query: Url query delimiter
        :type query: str (default '?')

        :raises ValueError: If value can not be parsed.

        :return: json response
        :rtype: dict
        """
        query_dict = QueryDict('', mutable=True)
        query_dict.update(parameters)
        if '?' in self.url:
            self.cache_url = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.cache_url = f'{self.url}{query}{query_dict.urlencode()}'

        # We are using another async session context manager
        async with self.session.get(self.cache_url, raise_for_status=True) as response:
            # Some servers (Arcrest...) send bad json, so disable validation
            return await response.json(content_type=None)

    async def extract_geometry(self, feature: dict, arc: bool = False):
        """Extract GEOS geometry from feature. Don't raise error if none found.

        :param parameters: parameters to urlencode
        :type parameters: dict

        :param arc: If geometry in arcgis format
        :type arc: bool
        """
        try:
            if arc:
                feature = arcgis2geojson(feature)
            self.geometry = GEOSGeometry(json.dumps(feature))
            self.geometry.srid = self.geometry.srid
        except IndexError:
            LOGGER.error(f"No geometry found for: {self.key}")
