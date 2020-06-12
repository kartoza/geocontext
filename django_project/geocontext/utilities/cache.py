from datetime import datetime, timedelta
import pytz

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


def retrieve_cache(service_util: ServiceUtil) -> Cache:
    """Retrieve closest valid cache from point.

    Filters for distance from query, cache expiry and service key.

    :param service_util: ServiceUtil instance
    :type service_util: ServiceUtil

    :returns: cache on None
    :rtype: cache or None
    """
    geometry = transform(service_util.geometry, 3857)
    return Cache.objects.filter(
                geometry__dwithin=(geometry, service_util.search_dist)
            ).filter(
                service=Service.objects.get(key=service_util.key),
                expired_time__gte=datetime.utcnow().replace(tzinfo=pytz.UTC),
            ).annotate(
                distance=Distance("geometry", geometry)
            ).order_by(
                "distance"
            ).first()
