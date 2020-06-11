from asyncio import ensure_future, gather
import json
import logging

import aiohttp
from arcgis2geojson import arcgis2geojson
from asgiref.sync import async_to_sync
from django.contrib.gis.geos import GEOSGeometry, Point
from django.http import QueryDict

from geocontext.models.service import Service
from geocontext.utilities.geometry import transform, get_bbox


LOGGER = logging.getLogger(__name__)


@async_to_sync
async def retrieve_service_value(service_utils: list) -> list:
    """Fetch data and loads into ServiceUtil instance using async aiohttp session.

    :param service_utils: ServiceUtil list
    :type service_utils: list

    :return: List of ServiceUtil with values
    :rtype: list
    """
    conn = aiohttp.TCPConnector(limit=100)
    timeout = aiohttp.ClientTimeout(total=20, connect=2)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = []
        for service_util in service_utils:
            tasks.append(ensure_future(service_util.retrieve_value(session)))
        new_service_utils = await gather(*tasks)
    return new_service_utils


class ServiceUtil():
    """Async service methods. Init method calls ORM / blocking functions.
    """
    def __init__(self, service_key: str, point: Point, dist: float = 10.0):
        """Load object. Prepare geometry. This __init__ is async blocking.

        :param service_key: service_key
        :type service_key: str

        :param point: Query coordinate
        :type point: Point

        :param dist: Search distance query overide service (default=10.0).
        :type dist: int
        """
        # Unpack model into attributes
        service_dict = Service.objects.filter(key=service_key).values().first()
        for key, val in service_dict.items():
            setattr(self, key, val)

        # Group associated with this instance
        self.group_key = None

        # Add Cache model params
        self.source_uri = None
        self.value = None
        self.session = None

        # Search distance query overrides service in model - else default 10m
        if dist != 10.0:
            self.search_dist = dist
        elif self.search_dist is None:
            self.search_dist = 10

        # Default geometry is point in service SRID - all queries/bbox in native srid
        self.geometry = transform(point, self.srid)

        # Calculate bbox - not async so call now
        self.bbox = get_bbox(self.geometry)

    async def retrieve_value(self, session: aiohttp.ClientSession) -> bool:
        """Load context value and geometry from service.
        All exceptions / logging / nulls for all services handled here.

        :param session: shared http session
        :type session: aiohttp.ClientSession

        """
        self.session = session
        try:
            if self.query_type == 'WMS':
                await self.fetch_wms()
            elif self.query_type == 'WFS':
                await self.fetch_wfs()
            elif self.query_type == 'ArcREST':
                await self.fetch_arcrest()
            elif self.query_type == 'PLACENAME':
                await self.fetch_placename()
            else:
                LOGGER.error(f"'{self.query_type}' not implimented: {self.key}")
                self.value = None
        except IndexError:
            LOGGER.error(f"{self.source_uri} No features found for: {self.key}")
            self.value = None
        except Exception as e:
            LOGGER.error(f"{self.source_uri} failed for: {self.key} with: {e}")
            self.value = None
        return self

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

        await self.extract_geometry(json_response['results'][0]['geometry'], arc=True)

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
            self.source_uri = f'{self.url}&{query_dict.urlencode()}'
        else:
            self.source_uri = f'{self.url}{query}{query_dict.urlencode()}'

        # We are using another async session context manager
        async with self.session.get(self.source_uri, raise_for_status=True) as response:
            # Some servers (Arcrest...) send bad json, so disable validation
            return await response.json(content_type=None)

    async def extract_geometry(self, feature: dict, arc: bool = False):
        """Extract GEOS geometry from feature. Don't raise error if none found. Only log.

        :param feature: geojson future
        :type feature: dict

        :param arc: If geometry in arcgis format
        :type arc: bool
        """
        try:
            feature = arcgis2geojson(feature) if arc else feature
            self.geometry = GEOSGeometry(json.dumps(feature))
            self.geometry.srid = self.srid
        except Exception:
            LOGGER.error(f"No geometry found for: {self.key}")
