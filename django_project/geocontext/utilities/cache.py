from datetime import datetime, timedelta
import pytz

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import Distance

from geocontext.models.service import Service
from geocontext.models.cache import Cache
from geocontext.utilities.geometry import transform, flatten
from geocontext.utilities.service import ServiceUtil


def create_cache(service_util: ServiceUtil) -> Cache:
    """Add context value and projected 2d geometry to cache.

    :param service_util: ServiceUtil instance
    :type service_util: ServiceUtil

    :return: Context cache instance
    :rtype: Cache
    """
    service = Service.objects.get(key=service_util.key)
    expired_time = datetime.utcnow() + timedelta(seconds=service.cache_duration)
    cache = Cache(
        service=service,
        name=service.key,
        value=service_util.value,
        expired_time=expired_time.replace(tzinfo=pytz.UTC),
        source_uri=service_util.source_uri
    )
    if service_util.geometry:
        service_util.geometry = transform(service_util.geometry, 3857)
        service_util.geometry = flatten(service_util.geometry)
        cache.geometry = service_util.geometry

    cache.save()
    return cache


def retrieve_cache_valid(cache: Cache, service_util: ServiceUtil) -> Cache:
    """Retrieve valid cache from queryset for service_util point.

    Filters for expiry date and service key. Returns first value.
    If cache queryset is ordered by distance we get the closest value.

    :param service_util: ServiceUtil instance
    :type service_util: ServiceUtil

    :param cache: cache queryset
    :type cache: queryset

    :returns: cache on None
    :rtype: cache or None
    """
    return cache.objects.filter(
                service=Service.objects.get(key=service_util.key),
                expired_time__gte=datetime.utcnow().replace(tzinfo=pytz.UTC),
            ).first()


def retrieve_cache_geometry(geometry: GEOSGeometry, dist: float = 10) -> Cache:
    """Retrieve sorted cache queryset for all geometries within search distance.

    We use ST_dwithin first to make use of the spatial index for speed.
    Filters for search distance in meter - only in 2d for now.
    Returns results ordered in distance from point.

    :param geometry: GeosGeometry to calculate distance to
    :type geometry: GeosGeometry

    :param dist: Distance in meters
    :type dist: float

    :returns: cache queryset
    :rtype: queryset
    """
    # Dwithin speeds op distance query but must be in the same SRID as geometry field
    geometry = transform(geometry, 3857)
    return Cache.objects.filter(
        geometry__dwithin=(geometry, dist)
    ).annotate(
        distance=Distance("geometry", geometry)
    ).order_by("distance")
