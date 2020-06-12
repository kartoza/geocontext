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
            tasks.append(ensure_future(service_util.retrieve_values(session)))
        new_service_utils = await gather(*tasks)
    return new_service_utils


class ServiceUtil():
    """Async service methods. Init method calls ORM / blocking functions.
    """
    def __init__(self, service_key: str, point: Point, search_dist: float):
        """Load object. Prepare geometry. This __init__ is async blocking.

        :param service_key: service_key
        :type service_key: str
        :param point: Query coordinate
        :type point: Point
        :param search_dist: Search distance query overide service (default=10.0).
        :type search_dist: int
        """
        service_dict = Service.objects.filter(key=service_key).values().first()
        for key, val in service_dict.items():
            setattr(self, key, val)

        if search_dist != 10.0:
            self.search_dist = search_dist
        elif self.search_dist is None:
            self.search_dist = 10
        self.point = transform(point, self.srid)
        self.bbox = get_bbox(self.point, self.search_dist)
        self.results = [{'value': None, 'geometry': self.point}]
        self.max_features = 10
        self.source_uri = None
        self.group_key = None
        self.session = None

    async def retrieve_values(self, session: aiohttp.ClientSession) -> bool:
        """Load context value and geometry from service.
        Service exceptions / logging handled here.

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
            elif self.query_type == 'PlaceName':
                await self.fetch_placename()
            else:
                LOGGER.error(f"'{self.query_type}' not implimented: {self.key}")
        except IndexError:
            LOGGER.error(f"'{self.source_uri}' No features found for: {self.key}")
        except Exception as e:
            LOGGER.error(f"'{self.source_uri}' failed for: {self.key} with: {e}")
        return self

    async def fetch_wms(self):
        """Fetch WMS value"""
        parameters = {
            'SERVICE': self.query_type,
            'INFO_FORMAT': 'application/json',
            'FEATURE_COUNT': self.max_features,
            'LAYERS': self.layer_typename,
            'QUERY_LAYERS': self.layer_typename,
            'BBOX': self.bbox,
            'WIDTH': 101,
            'HEIGHT': 101
        }
        if self.service_version in ['1.0.0', '1.1.0', '1.1.1']:
            parameters['REQUEST'] = 'feature_info'
            parameters['X'] = 50
            parameters['Y'] = 50
        elif self.service_version in ['1.3.0']:
            parameters['REQUEST'] = 'GetFeatureInfo'
            parameters['I'] = 50
            parameters['j'] = 50
        else:
            LOGGER.error(f"'{self.service_version}' not a supported WMS service.")

        json_response = await self.request_data(parameters)
        await self.save_features(json_response['features'])

    async def fetch_wfs(self):
        """Fetch WFS value. Try intersect else buffer with search distance."""
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
            'OUTPUTFORMAT': 'application/json',
            'MAXFEATURES': self.max_features,
            'VERSION': self.service_version,
            'TYPENAME': self.layer_typename,
            'FILTER': layer_filter,
            'PROPERTYNAME': f'({self.layer_name})',
        }

        json_response = await self.request_data(parameters)
        if len(json_response['features']) != 0:
            await self.save_features(json_response['features'])
        else:
            LOGGER.info(f"WFS intersect filter failed: '{self.key}' - attempt bbox")
            parameters = {
                'SERVICE': 'WFS',
                'REQUEST': 'GetFeature',
                'OUTPUTFORMAT': 'application/json',
                'MAXFEATURES': self.max_features,
                'VERSION': self.service_version,
                'TYPENAME': self.layer_typename,
                'BBOX': self.bbox
            }
            json_response = await self.request_data(parameters)
            await self.save_features(json_response['features'])

    async def fetch_arcrest(self):
        """Fetch ArcRest value"""
        parameters = {
            'f': 'json',
            'geometryType': 'esriGeometryPoint',
            'geometry': f'{{{{x: {self.point.x}, y: {self.point.y}}}}}',
            'layers': self.layer_name,
            'imageDisplay': '100,100,96',
            'tolerance': '1',
            'mapExtent': self.bbox,
            'returnGeometry': 'true',
            'maxRecordCount': self.max_features
        }
        json_response = await self.request_data(parameters, query='identify?')
        await self.save_features(json_response['results'])

    async def fetch_placename(self):
        """Fetch Placename value"""
        parameters = {
            'lat': str(self.point.y),
            'lng': str(self.point.x),
            'username': str(self.username),
        }
        json_response = await self.request_data(parameters)
        await self.save_features(json_response['geonames'])

    async def request_data(self, parameters: dict, query: str = '?') -> dict:
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

    async def save_features(self, features: list):
        """Find and store results: {value:geometry} attribute.

        :param feature: geojson futures list
        :type feature: dict
        """
        result = {}
        for feature in features:
            try:
                if 'properties' in feature:
                    result['value'] = feature['properties'][self.layer_name]
                else:
                    result['value'] = feature[self.layer_name]
            except Exception:
                LOGGER.error(f"No value found for feature in: '{self.key}'")
                continue

            try:
                if self.query_type == 'ArcREST':
                    geometry = arcgis2geojson(feature['geometry'])
                else:
                    geometry = feature['geometry']
                result['geometry'] = GEOSGeometry(json.dumps(geometry))
                result['geometry'].srid = self.srid
            except Exception:
                LOGGER.error(f"No geometry found for feature in: {self.key}")
                result['geometry'] = self.point

            # Clear default default Null result list on the first value found
            if self.results[0]['value'] is None and result['value'] is not None:
                self.results = []
            self.results.append(result)
