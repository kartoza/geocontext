# coding=utf-8
"""Docstring here."""
from datetime import datetime

import pytz
from django.contrib.gis.geos import Point

from geocontext.models import ContextServiceRegistry, ContextCache
from geocontext.utilities import convert_coordinate, generalize_point


def retrieve_context(x, y, service_registry_key, srid=4326):
    """Retrieve context from point x, y.

    :param x: X coordinate
    :type x: float

    :param y: Y Coordinate
    :type y: float

    :param service_registry_key: The key of service registry.
    :type service_registry_key: basestring

    :param srid: Spatial Reference ID
    :type srid: int

    :returns: Geometry of the context and the value.
    :rtype: (GEOSGeometry, basestring)
    """
    if srid != 4326:
        point = Point(*convert_coordinate(x, y, srid, 4326), srid=4326)
    else:
        point = Point(x, y, srid=4326)

    # Check in cache
    service_registry = ContextServiceRegistry.objects.get(
        key=service_registry_key)
    if not service_registry:
        raise Exception(
            'Service Registry is not Found for %s' % service_registry_key)

    # Generalize to improve cache hits is service requires
    point = generalize_point(point, service_registry)

    caches = ContextCache.objects.filter(
        service_registry=service_registry)

    for cache in caches:
        if cache.geometry:
            if cache.geometry.contains(point):
                current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
                is_expired = current_time > cache.expired_time
                if not is_expired:
                    return cache
                else:
                    # No need to check the rest cache, since it always only 1
                    # cache that intersect for a point.
                    cache.delete()
                    break

    # Can not find in caches, request from context service.
    val = service_registry.retrieve_context_value(point.x, point.y, point.srid)
    return val
