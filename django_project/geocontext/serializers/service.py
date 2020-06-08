from rest_framework import serializers
from geocontext.models.service import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer class for Service."""

    class Meta:
        model = Service
        fields = (
            'key',
            'name',
            'description',
            'url',
            'query_type',
            'result_regex',
            'time_to_live',
            'srid',
            'layer_typename',
            'service_version',
            'provenance',
            'notes',
            'licensing',
            'search_dist'
        )
