# coding=utf-8
"""View definitions."""

from distutils.util import strtobool

from django.core.serializers import serialize
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse, HttpResponse, Http404

from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response

from geocontext.forms import GeoContextForm
from geocontext.models.context_cache import ContextCache
from geocontext.models.context_collection import ContextCollection
from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.context_group_services import ContextGroupServices

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer)
from geocontext.serializers.context_cache import (
    ContextValueGeoJSONSerializer, ContextValueSerializer)

from geocontext.serializers.context_group import (
    ContextGroupValueSerializer, ContextGroupValue)
from geocontext.serializers.context_collection import (
    ContextCollectionValue, ContextCollectionValueSerializer)

from geocontext.models.utilities import retrieve_context


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


class ContextGroupValueView(views.APIView):
    """API view for Context Group Value."""
    def get(self, request, x, y, context_group_key):
        # Parse location
        x = float(x)
        y = float(y)
        context_group_value = ContextGroupValue(x, y, context_group_key)
        context_group_value_serializer = ContextGroupValueSerializer(
            context_group_value)
        return Response(context_group_value_serializer.data)


class ContextCollectionValueView(views.APIView):
    """API view for Context Collection Value."""
    def get(self, request, x, y, context_collection_key):
        # Parse location
        x = float(x)
        y = float(y)
        context_collection_value = ContextCollectionValue(
            x, y, context_collection_key)
        context_collection_value_serializer = ContextCollectionValueSerializer(
            context_collection_value)
        return Response(context_collection_value_serializer.data)


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
