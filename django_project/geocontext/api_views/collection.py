from rest_framework import views
from rest_framework.response import Response

from geocontext.serializers.utilities import CollectionValues
from geocontext.serializers.collection import CollectionValueSerializer


class CollectionAPIView(views.APIView):
    """Retrieving values from context collection matching:
    x (long), y (lat) collection key and optional SRID var (default use: 4326)
    """
    def get(self, request, x, y, collection_key, srid=4326):
        collection_values = CollectionValues(x, y, collection_key, srid)
        try:
            collection_values.populate_collection_values()
        except Exception as e:
            return Response(f"Server exception: {e}")
        collection_value_serializer = CollectionValueSerializer(collection_values)
        return Response(collection_value_serializer.data)
