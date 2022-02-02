"""Views for Geocontext V1 urls - TODO: depreciate"""

from distutils.util import strtobool
import psycopg2

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from rest_framework import generics, status, views
from rest_framework.response import Response

from geocontext.forms import GeoContextForm
from geocontext.models.service import Service
from geocontext.serializers.service import ServiceSerializer
from geocontext.utilities.geometry import parse_coord
from geocontext.utilities.worker import Worker


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
    def get(self, request, x, y, srid=4326, tolerance: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            worker = Worker('', '', point, tolerance, '')
            caches = worker.retrieve_caches(Service.objects.all())
            data = worker.nest_caches(caches)
            with_geometry = self.request.query_params.get('with-geometry', 'True')
            if strtobool(with_geometry):
                data = worker.serialize_geojson(data)
            return Response(data)
        except Exception:
            return Response("Server error", status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupAPIView(views.APIView):
    """Retrieve values from context group matching:  x (long), y (lat) group key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, group_key, srid=4326, tolerance: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            data = Worker('group', group_key, point, tolerance, 'json').retrieve_all()
            # For compatibility with V1 naming conventions
            data['service_registry_values'] = data.pop('services')
            return Response(data)
        except Exception as e:
            return Response(f"Server error {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollectionAPIView(views.APIView):
    """Retrieve values from context collection matching: x (long), y (lat) collection key.
    Catch any exception in populating values
    """
    def get(self, request, x, y, collection_key, srid=4326, tolerance: float = 10.0):
        try:
            point = parse_coord(x, y, srid)
            worker = Worker('collection', collection_key, point, tolerance, 'json')
            data = worker.retrieve_all()
            # For compatibility with V1 naming conventions
            data['context_group_values'] = data.pop('groups')
            for group in data['context_group_values']:
                group['service_registry_values'] = group.pop('services')
            return Response(data)
        except Exception as e:
            return Response(
                f"Server error {e}", status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            tolerance = cleaned_data.get('service_key', 10.0)
            point = parse_coord(x, y, srid)
            worker = Worker('service', service_key, point, tolerance, 'geojson')
            data = worker.retrieve_all()
            return HttpResponse(data, content_type='application/json')
        else:
            raise Http404('Sorry! We could not find context for your point!')
    else:
        form = GeoContextForm(initial={'srid': 4326})
        return render(request, 'geocontext/get_service.html', {'form': form})
