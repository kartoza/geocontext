from rest_framework import views
from rest_framework.response import Response

from geocontext.serializers.collection import ContextCollectionValueSerializer
from geocontext.serializers.utilities import CollectionValues


class ContextCollectionValueAPIView(views.APIView):
    """Retrieving value based on a point (x, y) and a context collection key.
    """
    def get(self, request, x, y, context_collection_key, srid=4326):
        collection_values = CollectionValues(x, y, context_collection_key, srid)
        collection_values.populate_collection_values()
        collection_serializer = ContextCollectionValueSerializer(collection_values)
        return Response(collection_serializer.data)
