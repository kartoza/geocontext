# coding=utf-8
"""View definitions."""

import pytz
from datetime import datetime
from distutils.util import strtobool

from django.contrib.gis.geos import Point
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.core.serializers import serialize

from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response

from geocontext.utilities import convert_coordinate

from geocontext.models.context_cache import ContextCache
from geocontext.models.context_collection import ContextCollection
from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.context_group_services import ContextGroupServices

from geocontext.forms import GeoContextForm

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer)
from geocontext.serializers.context_cache import (
    ContextValueGeoJSONSerializer, ContextValueSerializer)


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
    caches = ContextCache.objects.filter(
        service_registry=service_registry)

    for cache in caches:
        if cache.geometry.contains(point):
            if datetime.utcnow().replace(tzinfo=pytz.UTC) < cache.expired_time:
                return cache
            else:
                # No need to check the rest cache, since it always only 1
                # cache that intersect for a point.
                cache.delete()
                break

    # Can not find in caches, request from context service.
    return service_registry.retrieve_context_value(x, y, srid)


def get_context(request):
    """Get context view."""
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = GeoContextForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            cleaned_data = form.cleaned_data
            x = cleaned_data['x']
            y = cleaned_data['y']
            srid = cleaned_data.get('srid', 4326)
            service_registry_key = cleaned_data['service_registry_key']
            result = retrieve_context(x, y, service_registry_key, srid)
            fields = ('value', 'key')
            if result:
                return HttpResponse(
                    serialize(
                        'geojson',
                        [result],
                        geometry_field='geometry_multi_polygon',
                        fields=fields),
                    content_type='application/json')
            else:
                raise Http404(
                    'Sorry! We could not find context for your point!')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = GeoContextForm(initial={'srid': 4326})

    return render(request, 'geocontext/get_context.html', {'form': form})


class ContextServiceRegistryList(generics.ListCreateAPIView):
    """List all service registry or create new one."""
    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextServiceRegistryDetail(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a service registry."""

    lookup_field = 'key'

    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextCacheList(generics.ListAPIView):
    """List all context cache."""
    queryset = ContextCache.objects.all()
    serializer_class = ContextValueGeoJSONSerializer


class ContextValueGeometryList(views.APIView):
    """List all context cache based on point."""

    def get(self, request, x, y, csr_keys=None, format=None):
        # Parse location
        x = float(x)
        y = float(y)
        # List all CSR keys
        if not csr_keys:
            context_service_registries = ContextServiceRegistry.objects.all()
            csr_keys = [o.key for o in context_service_registries]
        else:
            csr_keys = csr_keys.split(',')

        with_parent = self.request.query_params.get(
            'with-parent', 'False')

        if len(csr_keys) == 1 and strtobool(with_parent):
            hierarchy_csr_keys = [csr_keys[0]]
            current_csr = ContextServiceRegistry.objects.get(
                key=csr_keys[0])
            while current_csr is not None:
                current_csr = current_csr.parent
                if current_csr is not None:
                    hierarchy_csr_keys.append(current_csr.key)
                else:
                    break
            csr_keys = hierarchy_csr_keys

        context_caches = []
        for csr_key in csr_keys:
            context_cache = retrieve_context(x, y, csr_key)
            context_caches.append(context_cache)
        with_geometry = self.request.query_params.get('with-geometry', 'True')
        if strtobool(with_geometry):
            serializer = ContextValueGeoJSONSerializer(
                context_caches, many=True)
        else:
            serializer = ContextValueSerializer(context_caches, many=True)
        return Response(serializer.data)


def collection_value_list(request, x, y, collection_key):
    # Parse location
    x = float(x)
    y = float(y)
    data = {}
    context_collection = get_object_or_404(
        ContextCollection, key=collection_key)
    data['key'] = collection_key
    data['name'] = context_collection.name
    data['context_groups'] = []
    collection_groups = CollectionGroups.objects.filter(
        context_collection=context_collection).order_by('order')
    for collection_group in collection_groups:
        context_group = collection_group.context_group
        context_group_data = {
            'key': context_group.key,
            'name': context_group.name,
        }
        context_group_services = ContextGroupServices.objects.filter(
            context_group=context_group).order_by('order')
        context_caches = []
        for context_group_service in context_group_services:
            context_service_registry_key = \
                context_group_service.context_service_registry.key
            context_cache = retrieve_context(
                x, y, context_service_registry_key)
            context_caches.append(context_cache)
        context_cache_serializer = ContextValueSerializer(
            context_caches, many=True)
        context_group_data['context_service_registries'] = \
            context_cache_serializer.data
        data['context_groups'].append(context_group_data)

    return JsonResponse(data)
