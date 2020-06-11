from datetime import datetime, timedelta
import logging
import pytz

from django.contrib.gis.measure import Distance

from geocontext.models.service import Service
from geocontext.models.cache import Cache
from geocontext.utilities.geometry import transform, flatten


LOGGER = logging.getLogger(__name__)


def create_cache(service_util) -> Cache:
    """Add context value and projected 2d geometry to cache.

    We use EPSG:3857 to optimise cache distance queries.

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

    if service_util.geometry:
        service_util.geometry = transform(service_util.geometry, 3857)
        service_util.geometry = flatten(service_util.geometry)
        cache.geometry = service_util.geometry

    cache.source_uri = service_util.source_uri if service_util.source_uri else None

    cache.save()
    cache.refresh_from_db()
    return cache


def retrieve_cache(service_util) -> Cache:
    """Try to retrieve service cache for service_util point.

    Filters for search distance and expiry date.
    Distance search in meter - only in 2d for now.

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
    ).first()
    return caches
