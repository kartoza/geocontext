from datetime import datetime, timedelta
import pytz

from django.contrib.gis.db.models.functions import Distance

from geocontext.models.service import Service
from geocontext.models.cache import Cache
from geocontext.utilities.geometry import transform, flatten
from geocontext.utilities.service import ServiceUtil


def retrieve_cache(service_util: ServiceUtil) -> Cache:
    """Retrieve closest valid cache from point. Filters for cache expiry and service key.

    :param service_util: ServiceUtil instance
    :type service_util: ServiceUtil
    :returns: cache on None
    :rtype: cache or None
    """
    point = transform(service_util.point, Cache.srid)
    return Cache.objects.filter(
                        geometry__dwithin=(point, service_util.tolerance)
                    ).filter(
                        service=Service.objects.get(key=service_util.key),
                        expired_time__gte=datetime.utcnow().replace(tzinfo=pytz.UTC),
                    ).annotate(
                        distance=Distance('geometry', point)
                    ).order_by(
                        'distance'
                    ).first()


def create_cache(service_util: ServiceUtil) -> Cache:
    """Parse and find closest geometries to query, add to cache with value and return.

    :param service_util: ServiceUtil instance
    :type service_util: ServiceUtil
    :return: Cache instance
    :rtype: Cache
    """
    expired_time = datetime.utcnow() + timedelta(seconds=service_util.cache_duration)
    cache = Cache(
        service=Service.objects.get(key=service_util.key),
        name=service_util.key,
        value=service_util.value,
        expired_time=expired_time.replace(tzinfo=pytz.UTC),
        source_uri=service_util.source_uri,
        geometry=flatten(transform(service_util.geometry, Cache.srid))
    )
    cache.save()
    return cache
