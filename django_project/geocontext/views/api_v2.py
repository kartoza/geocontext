from django.core.serializers import serialize
from rest_framework import status
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.views import APIView

from geocontext.serializers.collection import CollectionValueSerializer
from geocontext.serializers.group import GroupValueSerializer
from geocontext.utilities.collection import CollectionValues
from geocontext.utilities.geometry import parse_coord
from geocontext.utilities.service import retrieve_service_value, ServiceUtil
from geocontext.utilities.cache import create_cache, retrieve_cache
from geocontext.utilities.group import GroupValues


def get_data(request):
    """
    Generic function to parse Geocontext keyword get arguments
    """
    x = request.GET.get('x', None)
    y = request.GET.get('y', None)
    key = request.GET.get('key', None)
    srid = request.GET.get('srid', 4326)
    search_dist = request.GET.get('search_dist', 10.0)
    data = {
        'x': x,
        'y': y,
        'srid': srid,
        'key': key,
        'search_dist': search_dist
    }
    for key, val in data.items():
        if val is None:
            raise KeyError(f'Required request argument missing: {key}')
    return data


class ServiceAPIView(APIView):
    """
    Geocontext API v2 endpoint for service queries.
    """
    def get(self, request):
        try:
            data = get_data(request)
            point = parse_coord(x=data['x'], y=data['y'], srid=data['srid'])
            service_util = ServiceUtil(data['key'], point, data['search_dist'])
            cache = retrieve_cache(service_util)
            if cache is None:
                new_service_util = retrieve_service_value([service_util])
                if new_service_util[0].value is not None:
                    cache = create_cache(new_service_util)
            return HttpResponse(serialize(
                                    'json',
                                    [cache],
                                ),
                                content_type='application/json')
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupAPIView(APIView):
    """
    Geocontext API v2 endpoint for group queries.
    """
    def get(self, request):
        try:
            data = get_data(request)
            point = parse_coord(x=data['x'], y=data['y'], srid=data['srid'])
            group_values = GroupValues(data['key'], point, data['search_dist'])
            group_values.populate_group_values()
            group_value_serializer = GroupValueSerializer(group_values)
            response_data = group_value_serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class CollectionAPIView(APIView):
    """
    Geocontext API v2 endpoint for collection queries.
    """
    def get(self, request):
        try:
            data = get_data(request)
            point = parse_coord(x=data['x'], y=data['y'], srid=data['srid'])
            collection_values = CollectionValues(data['key'], point, data['search_dist'])
            collection_values.populate_collection_values()
            collection_value_serializer = CollectionValueSerializer(collection_values)
            response_data = collection_value_serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
