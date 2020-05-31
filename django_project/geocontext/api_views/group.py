from rest_framework import views
from rest_framework.response import Response

from geocontext.serializers.group import GroupSerializer
from geocontext.serializers.utilities import GroupValues


class GroupAPIView(views.APIView):
    """Retrieving value based on a point (x, y, srid) and a group key."""
    def get(self, request, x, y, group_key, srid=4326):
        group_values = GroupValues(x, y, group_key, srid)
        group_values.self.populate_group_values()
        group_serializer = GroupSerializer(group_values)
        return Response(group_serializer.data)
