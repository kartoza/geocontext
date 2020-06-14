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

from geocontext.forms import GeoContextForm
from geocontext.models.service import Service
from geocontext.serializers.cache import CacheGeoJSONSerializer, CacheSerializer
from geocontext.serializers.collection import CollectionValueSerializer
from geocontext.serializers.service import ServiceSerializer
from geocontext.serializers.group import GroupValueSerializer
from geocontext.utilities.cache import create_cache, retrieve_cache
from geocontext.utilities.collection import CollectionValues
from geocontext.utilities.geometry import parse_coord
from geocontext.utilities.group import GroupValues
from geocontext.utilities.service import retrieve_service_value, ServiceUtil


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
    def get(self, request, x, y, srid=4326, search_dist: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            services = Service.objects.all()
            service_keys = [o.key for o in services]
            caches = []
            for service_key in service_keys:
                service_util = ServiceUtil(service_key, point, search_dist)
                cache = retrieve_cache(service_util)
                caches.append(cache)
            with_geometry = self.request.query_params.get('with-geometry', 'True')
            if strtobool(with_geometry):
                serializer = CacheGeoJSONSerializer(caches, many=True)
            else:
                serializer = CacheSerializer(caches, many=True)
            return Response(serializer.data)
        except Exception:
            return Response("Server error", status.HTTP_400_BAD_REQUEST)
        if None in caches:
            return Response("No cache found", status.HTTP_400_BAD_REQUEST)


class GroupAPIView(views.APIView):
    """Retrieve values from context group matching:  x (long), y (lat) group key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, group_key, srid=4326, search_dist: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            group_values = GroupValues(group_key, point, search_dist)
            group_values.populate_group_values()
            group_value_serializer = GroupValueSerializer(group_values)
            return Response(group_value_serializer.data)
        except Exception as e:
            return Response(
                f"Could not fetch data: Server error {e}", status.HTTP_400_BAD_REQUEST)


class CollectionAPIView(views.APIView):
    """Retrieve values from context collection matching: x (long), y (lat) collection key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, collection_key, srid=4326, search_dist: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            collection_values = CollectionValues(collection_key, point, search_dist)
            collection_values.populate_collection_values()
            collection_value_serializer = CollectionValueSerializer(collection_values)
            return Response(collection_value_serializer.data)
        except Exception as e:
            return Response(
                f"Could not fetch data: Server error {e}", status.HTTP_400_BAD_REQUEST)


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
        point = parse_coord(x, y, 4326)
        cursor.callproc('finder', [point.x, point.y])
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
            service_key = cleaned_data['service_key']
            srid = cleaned_data.get('srid', 4326)
            search_dist = cleaned_data.get('service_key', 10.0)
            point = parse_coord(x, y, srid)
            service_util = ServiceUtil(service_key, point, search_dist)
            cache = retrieve_cache(service_util)
            if cache is None:
                new_service_util = retrieve_service_value([service_util])
                if new_service_util.value is not None:
                    caches = create_cache(new_service_util)
            fields = ('value', 'key')
            if cache:
                return HttpResponse(
                    serialize(
                        'geojson',
                        caches,
                        geometry_field='geometry_multi_polygon',
                        fields=fields),
                    content_type='application/json')
            else:
                raise Http404('Sorry! We could not find context for your point!')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = GeoContextForm(initial={'srid': 4326})

    return render(request, 'geocontext/get_service.html', {'form': form})
