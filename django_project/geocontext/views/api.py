# coding=utf-8
"""View definitions."""

from distutils.util import strtobool

from django.core.serializers import serialize
from django.shortcuts import render
from django.http import HttpResponse, Http404

from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response

from geocontext.forms import GeoContextForm
from geocontext.models.context_cache import ContextCache
from geocontext.models.context_service_registry import ContextServiceRegistry

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer)
from geocontext.serializers.context_cache import (
    ContextValueGeoJSONSerializer, ContextValueSerializer)

from geocontext.serializers.context_group import (
    ContextGroupValueSerializer, ContextGroupValue)
from geocontext.serializers.context_collection import (
    ContextCollectionValue, ContextCollectionValueSerializer)

from geocontext.models.utilities import retrieve_context


class ContextServiceRegistryListAPIView(generics.ListAPIView):
    """List all service registry or create new one."""
    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextServiceRegistryDetailAPIView(generics.RetrieveAPIView):
    """Retrieve, update, or delete a service registry."""

    lookup_field = 'key'

    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextCacheListAPIView(generics.ListAPIView):
    """List all context cache."""
    queryset = ContextCache.objects.all()
    serializer_class = ContextValueGeoJSONSerializer


class ContextValueGeometryListAPI(views.APIView):
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


class ContextGroupValueAPIView(views.APIView):
    """API view for Context Group Value."""
    def get(self, request, x, y, context_group_key):
        # Parse location
        x = float(x)
        y = float(y)
        context_group_value = ContextGroupValue(x, y, context_group_key)
        context_group_value_serializer = ContextGroupValueSerializer(
            context_group_value)
        return Response(context_group_value_serializer.data)


class ContextCollectionValueAPIView(views.APIView):
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
