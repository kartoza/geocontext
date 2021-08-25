"""
Module with async functions and async service class for retrieving external data
"""
import asyncio
from asyncio import ensure_future, gather
from concurrent.futures.process import ProcessPoolExecutor
from datetime import datetime as dt
from datetime import timedelta as td
from functools import partial
import logging
from pytz import UTC
import sys

import aiohttp
from asgiref.sync import async_to_sync
from django.contrib.gis.geos import Point
from django.forms.models import model_to_dict
from django.http import QueryDict

from geocontext.models.cache import Cache
from geocontext.models.service import Service
from geocontext.utilities.geometry import get_bbox, parse_geometry, transform
from geocontext.utilities.strings import strip_whitespace

LOGGER = logging.getLogger(__name__)


@async_to_sync
async def async_retrieve_services(async_services: list) -> list:
    """Load AsyncService instance and load with external data using async aiohttp session.

    :param async_services: AsyncService list
    :type async_services: list

    :return: List of AsyncService with values
    :rtype: list
    """
    conn = aiohttp.TCPConnector(limit=100)
    timeout = aiohttp.ClientTimeout(total=20, connect=2)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        tasks = [ensure_future(util.retrieve_values(session)) for util in async_services]
        new_async_services = await gather(*tasks)
    return new_async_services


class AsyncService():
    """
    Async service methods to collect external data.
    """

    def __init__(self, service: Service, point: Point, tolerance: float):
        """Load object

        :param service: Service instance
        :type service: dict
        :param point: Query coordinate
        :type point: Point
        :param tolerance: Tolerance of query in meter (default=10.0).
        :type tolerance: int
        """
        self.service = service
        # We unpack the model attributes for this class
        for key, val in model_to_dict(service).items():
            setattr(self, key, val)

        # Service query configuration
        if tolerance != 10.0:
            self.tolerance = tolerance
        elif self.tolerance is None:
            self.tolerance = 10.0
        self.point = transform(point, self.srid)
        self.point_cache = transform(point, Cache.srid)
        self.max_features = 10
        self.source_uri = None
        self.group_key = None
        self.session = None
        self.expire = dt.utcnow().replace(tzinfo=UTC) + td(seconds=self.cache_duration)

        # Data that can retrieved form service - geometry defaults to query point
        self.value = None
        self.geometry = self.point

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
                LOGGER.error(f'"{self.query_type}" not implimented: {self.key}')
        except IndexError:
            LOGGER.error(f'"{self.source_uri}" No features found for: {self.key}')
        except Exception as e:
            LOGGER.error(f'{self.source_uri}" failed for: {self.key} with: {e}')

        # Return AsyncService instance with attributes loaded from service
        return self

    async def fetch_wms(self):
        """Fetch WMS value"""
        bbox = get_bbox(self.point, self.tolerance)
        parameters = {
            'SERVICE': self.query_type,
            'INFO_FORMAT': 'application/json',
            'LAYERS': self.layer_typename,
            'QUERY_LAYERS': self.layer_typename,
            'FEATURE_COUNT': self.max_features,
            'BBOX': bbox,
            'WIDTH': 101,
            'HEIGHT': 101
        }
        if self.service.key == 'river_name':
            parameters.update({
                'REQUEST': 'GetMap',
                'srs': 'EPSG:3857',
                'BBOX': '1831085.1652849577,-4139213.1300405697,3657706.640180942,-2526627.791405775',
                'format': 'geojson',
                'viewparams': 'latitude:{};longitude:{}'.format(self.point.x, self.point.y)
            })
        elif self.service_version in ['1.0.0', '1.1.0', '1.1.1']:
            parameters.update({
                'REQUEST': 'feature_info',
                'X': 50,
                'Y': 50
            })
        elif self.service_version in ['1.3.0']:
            parameters.update({
                'REQUEST': 'GetFeatureInfo',
                'I': 50,
                'j': 50
            })
        else:
            LOGGER.error(f"'{self.service_version}' not a supported WMS service.")
            return

        json_response = await self.request_data(parameters)

        await self.save_features(json_response['features'])

    async def fetch_wfs(self):
        """Fetch WFS value. Try intersect else buffer with specified tolerance."""
        parameters = {
            'SERVICE': 'WFS',
            'REQUEST': 'GetFeature',
            'OUTPUTFORMAT': 'application/json',
            'VERSION': self.service_version,
            'TYPENAME': self.layer_typename,
            'PROPERTYNAME': f'({self.layer_name})',
            'FILTER': (
                '<Filter xmlns="http://www.opengis.net/ogc" '
                'xmlns:gml="http://www.opengis.net/gml"> '
                f'<Intersects><PropertyName>geom</PropertyName>'
                f'<gml:Point srsName="EPSG:{self.point.srid}">'
                f'<gml:coordinates>{self.point.x},{self.point.y}'
                '</gml:coordinates></gml:Point></Intersects></Filter>'
            )
        }
        if self.service_version in ['1.0.0', '1.1.0', '1.3.0']:
            parameters.update({
                'count': self.max_features
            })
        elif self.service_version in ['2.0.0']:
            parameters.update({
                'maxFeatures': self.max_features
            })
        else:
            LOGGER.error(f"'{self.service_version}' not a supported WFS service.")
            return

        json_response = await self.request_data(parameters)
        if len(json_response['features']) != 0:
            return await self.save_features(json_response['features'])

        LOGGER.info(f'WFS intersect filter failed: "{self.key}" - attempt bbox')
        parameters.pop('FILTER')
        bbox = get_bbox(self.point, self.tolerance)
        parameters.update({
            'BBOX': bbox,
            'SRSNAME': f'EPSG:{self.point.srid}'
        })

        json_response = await self.request_data(parameters)
        await self.save_features(json_response['features'])

    async def fetch_arcrest(self):
        """Fetch ArcRest value"""
        bbox = get_bbox(self.point, self.tolerance)
        parameters = {
            'f': 'json',
            'geometryType': 'esriGeometryPoint',
            'geometry': f'{{{{x: {self.point.x}, y: {self.point.y}}}}}',
            'layers': self.layer_name,
            'imageDisplay': '100,100,96',
            'tolerance': '1',
            'mapExtent': bbox,
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
        query = '&' if '?' in self.url and query == '?' else query
        self.source_uri = f'{self.url}{query}{query_dict.urlencode()}'

        # Async session - disable validation - some servers, like ArrcREST, send bad json.
        async with self.session.get(self.source_uri, raise_for_status=True) as response:
            return await response.json(content_type=None)

    async def save_features(self, features: list):
        """Find and store results: {value:geometry} attribute.

        :param feature: geojson futures list
        :type feature: dict
        """
        results = []
        for feature in features:
            result = {}
            # We don't want to raise error if one feature fails - just skip
            try:
                if 'properties' in feature:
                    result['val'] = strip_whitespace(feature['properties'][self.layer_name])
                else:
                    result['val'] = strip_whitespace(feature[self.layer_name])
            except Exception:
                LOGGER.error(f'No value found for feature in: "{self.key}"')
                continue

            # We don't want to raise error if no geometry found - don't parse in async
            try:
                result['geom'] = feature['geometry']
            except Exception:
                LOGGER.info(f'No geometry found for feature in: "{self.key}"')

            results.append(result)

        # Multiple value/geometry results per query possible - find nearest
        if len(results) != 0:
            await self.nearest_geometry_value(results)

    async def nearest_geometry_value(self, results: list) -> list:
        """Find value and geometry closest to query in async_service results list.
        Large complex geometries block async - so spin up processes for these.

        :param results: result list of val:geom dicts
        :type results: list
        """
        dist = 1000000
        self.value = results[0]['val']
        for result in results:
            arc = True if self.query_type == 'ArcREST' else False
            func = partial(parse_geometry, result['geom'], arc)

            # Processes are costly - only for large objects (threshold could be tweaked)
            if sys.getsizeof(result['geom']) > 100:
                loop = asyncio.get_running_loop()
                exe = ProcessPoolExecutor(max_workers=1)
                geometry = await loop.run_in_executor(exe, func)
            else:
                geometry = func()
            if geometry is not None:
                new_dist = self.point.distance(geometry)
                if new_dist < dist:
                    dist = new_dist
                    self.value = result['val']
                    self.geometry = geometry
