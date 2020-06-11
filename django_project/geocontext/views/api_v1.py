# We keep V1 api views for compatability for now

from distutils.util import strtobool
import psycopg2

from django.core.serializers import serialize
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

from rest_framework import status
from rest_framework import generics
from rest_framework import views
from rest_framework.response import Response

from geocontext.models.service import Service
from geocontext.utilities.service import (
    async_retrieve_service,
    ServiceUtil,
    UtilArg
)
from geocontext.utilities.cache import (
    create_cache,
    retrieve_cache
)

from geocontext.forms import GeoContextForm
from geocontext.serializers.cache import CacheGeoJSONSerializer, CacheSerializer
from geocontext.serializers.collection import CollectionValueSerializer
from geocontext.serializers.service import ServiceSerializer
from geocontext.serializers.group import GroupValueSerializer
from geocontext.utilities.values import CollectionValues, GroupValues


class ServiceListAPIView(generics.ListAPIView):
    """List all context services."""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class ServiceDetailAPIView(generics.RetrieveAPIView):
    """Retrieve details of a context service."""
    lookup_field = 'key'
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class CacheListAPI(views.APIView):
    """Retrieving values from cache matching: x (long), y (lat)
    """
    def get(self, request, x, y, srid=4326):
        services = Service.objects.all()
        service_keys = [o.key for o in services]
        caches = []
        try:
            for service_key in service_keys:
                service_util = ServiceUtil(service_key, x, y, srid)
                cache = retrieve_cache(service_util)
                caches.append(cache)
        except Exception:
            return Response("Server error", status.HTTP_400_BAD_REQUEST)
        if None in caches:
            return Response("No cache found", status.HTTP_400_BAD_REQUEST)
        with_geometry = self.request.query_params.get('with-geometry', 'True')
        if strtobool(with_geometry):
            serializer = CacheGeoJSONSerializer(caches, many=True)
        else:
            serializer = CacheSerializer(caches, many=True)
        return Response(serializer.data)


class GroupAPIView(views.APIView):
    """Retrieve values from context group matching:  x (long), y (lat) group key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, group_key, srid=4326):
        group_values = GroupValues(x, y, group_key, srid)

        try:
            group_values.populate_group_values()
        except Exception as e:
            return Response(
                f"Could not fetch data: Server error {e}", status.HTTP_400_BAD_REQUEST)
        group_value_serializer = GroupValueSerializer(group_values)
        return Response(group_value_serializer.data)


class CollectionAPIView(views.APIView):
    """Retrieve values from context collection matching: x (long), y (lat) collection key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, collection_key, srid=4326):
        collection_values = CollectionValues(x, y, collection_key, srid)
        try:
            collection_values.populate_collection_values()
        except Exception as e:
            return Response(
                f"Could not fetch data: Server error {e}", status.HTTP_400_BAD_REQUEST)
        collection_value_serializer = CollectionValueSerializer(collection_values)
        return Response(collection_value_serializer.data)


class RiverNameAPIView(views.APIView):
    """Retrieve river name matching: x (long), y (lat).
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
                    f"dbname={db_name} user={db_user} host={db_host}"
                    f" password='{db_pass}' port={db_port}"
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


def get_service(request):
    """Get get_service view.

    :raises Http404: Can not find context
    :return: Form
    :rtype: GeoContextForm
    """
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
            service_key = cleaned_data['service_key']
            service_util = ServiceUtil(service_key, x, y, srid)
            cache = retrieve_cache(service_util)
            if cache is None:
                util_arg = UtilArg(group_key=None, service_util=service_util)
                new_util_arg = async_retrieve_service(util_arg)
                if new_util_arg.service_util.value is not None:
                    cache = create_cache(new_util_arg.service_util)
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
                raise Http404('Sorry! We could not find context for your point!')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = GeoContextForm(initial={'srid': 4326})

    return render(request, 'geocontext/get_service.html', {'form': form})
