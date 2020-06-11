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
            'layer_name',
            'layer_namespace',
            'layer_typename',
            'layer_workspace',
            'cache_duration',
            'srid',
            'service_version',
            'provenance',
            'notes',
            'licensing',
            'search_dist'
        )
