from rest_framework import views
from rest_framework.response import Response

from geocontext.serializers.collection import CollectionValueSerializer
from geocontext.serializers.utilities import CollectionValues


class CollectionValueAPIView(views.APIView):
    """Retrieving value based on a point (x, y) and a collection key.
    """
    def get(self, request, x, y, collection_key, srid=4326):
        collection_values = CollectionValues(x, y, collection_key, srid)
        collection_values.populate_collection_values()
        collection_serializer = CollectionValueSerializer(collection_values)
        return Response(collection_serializer.data)
