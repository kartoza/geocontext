from rest_framework import status
from rest_framework import views
from rest_framework.response import Response

from geocontext.serializers.utilities import GroupValues
from geocontext.serializers.group import GroupValueSerializer


class GroupAPIView(views.APIView):
    """Retrieving values from context group matching:
    x (long), y (lat) group key and optional SRID var (default use: 4326)
    """
    def get(self, request, x, y, group_key, srid=4326):
        group_values = GroupValues(x, y, group_key, srid)
        try:
            group_values.populate_group_values()
        except Exception:
            return Response("Could not fetch data", status.HTTP_400_BAD_REQUEST)
        group_value_serializer = GroupValueSerializer(group_values)
        return Response(group_value_serializer.data)
