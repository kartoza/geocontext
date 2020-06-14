from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from geocontext.serializers.collection import CollectionValueSerializer
from geocontext.utilities.collection import CollectionValues
from geocontext.utilities.geometry import parse_coord
from geocontext.utilities.service import retrieve_service_value, ServiceUtil


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


class CacheViewSet(APIView):
    """
    API endpoint for geocontext API v2 queries
    """
    def get(self, request):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ServiceViewSet(APIView):
    """
    API endpoint for geocontext API v2 queries
    """
    def get(self, request):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(APIView):
    """
    API endpoint for geocontext API v2 queries
    """
    def get(self, request):
        return Response(status=status.HTTP_400_BAD_REQUEST)


class CollectionViewSet(APIView):
    """
    API endpoint for geocontext API v2 queries
    """
    def get(self, request):
        try:
            data = get_data(request)
        except KeyError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        try:
            point = parse_coord(x=data['x'], y=data['y'], srid=data['srid'])
            collection_values = CollectionValues(data['key'], point, data['search_dist'])
            collection_values.populate_collection_values()
            collection_value_serializer = CollectionValueSerializer(collection_values)
            response_data = collection_value_serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(f"Server error {str(e)}", status.HTTP_400_BAD_REQUEST)
