# coding=utf-8
"""View definitions."""

from distutils.util import strtobool
import psycopg2

from django.core.serializers import serialize
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.conf import settings

from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response

from geocontext.forms import GeoContextForm
from geocontext.models.context_service_registry import ContextServiceRegistry

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer)
from geocontext.serializers.context_cache import (
    ContextValueGeoJSONSerializer, ContextValueSerializer)

from geocontext.serializers.context_group import (
    ContextGroupValueSerializer, ContextGroupValue)
from geocontext.serializers.context_collection import (
    ContextCollectionValue, ContextCollectionValueSerializer)

from geocontext.models.utilities import (
    ContextServiceRegistryUtils,
    retrieve_from_registry_util
)


class ContextServiceRegistryListAPIView(generics.ListAPIView):
    """List all context service registry."""
    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextServiceRegistryDetailAPIView(generics.RetrieveAPIView):
    """Retrieve a detail of a context service registry."""

    lookup_field = 'key'

    queryset = ContextServiceRegistry.objects.all()
    serializer_class = ContextServiceRegistrySerializer


class ContextValueGeometryListAPI(views.APIView):
    """List all current context cache based on point (x, y)."""

    def get(self, request, x, y, csr_keys=None):
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
            registry_utils = ContextServiceRegistryUtils(csr_key, x, y)
            cache = registry_utils.retrieve_context_cache()
            context_caches.append(cache)
        if None in context_caches:
            return Response('No cache found')
        with_geometry = self.request.query_params.get('with-geometry', 'True')
        if strtobool(with_geometry):
            serializer = ContextValueGeoJSONSerializer(
                context_caches, many=True)
        else:
            serializer = ContextValueSerializer(context_caches, many=True)
        return Response(serializer.data)


class ContextGroupValueAPIView(views.APIView):
    """Retrieving value based on a point (x, y) and a context group key."""
    def get(self, request, x, y, context_group_key):
        # Parse location
        x = float(x)
        y = float(y)
        context_group_value = ContextGroupValue(x, y, context_group_key)
        context_group_value_serializer = ContextGroupValueSerializer(
            context_group_value)
        return Response(context_group_value_serializer.data)


class ContextCollectionValueAPIView(views.APIView):
    """Retrieving value based on a point (x, y) and a context collection key.
    """
    def get(self, request, x, y, context_collection_key):
        # Parse location
        x = float(x)
        y = float(y)
        context_collection_value = ContextCollectionValue(
            x, y, context_collection_key)
        context_collection_value_serializer = ContextCollectionValueSerializer(
            context_collection_value)
        return Response(context_collection_value_serializer.data)


class RiverNameAPIView(views.APIView):
    """Retrieving river name based on a point (x, y)
    """
    def get(self, request, x, y):
        db_name = settings.RIVER_DATABASE['NAME']
        db_host = settings.RIVER_DATABASE['HOST']
        db_user = settings.RIVER_DATABASE['USER']
        db_pass = settings.RIVER_DATABASE['PASSWORD']
        db_port = 5432
        if not db_name or not db_host:
            raise Http404()
        try:
            conn = (
                psycopg2.connect(
                    "dbname=%s user=%s host=%s password='%s' port=%s" % (
                        db_name, db_user, db_host, db_pass, db_port
                    )
                )
            )
        except psycopg2.OperationalError:
            raise Http404()
        cursor = conn.cursor()
        cursor.callproc('finder', [x, y])
        results = cursor.fetchone()
        cursor.close()
        if results:
            return Response(results[0])
        else:
            raise Http404()


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
            registry_utils = ContextServiceRegistryUtils(service_registry_key, x, y, srid)
            cache = registry_utils.retrieve_context_cache()
            if cache is None:
                result = retrieve_from_registry_util(registry_utils)
                cache = registry_utils.create_context_cache(**result)
            fields = ('value', 'key')
            if cache:
                return HttpResponse(
                    serialize(
                        'geojson',
                        [cache],
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
