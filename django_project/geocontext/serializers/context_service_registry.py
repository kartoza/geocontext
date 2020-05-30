from rest_framework import serializers
from geocontext.models.context_service_registry import ContextServiceRegistry


class ContextServiceRegistrySerializer(serializers.ModelSerializer):
    """Serializer class for Context Service Registry."""

    class Meta:
        model = ContextServiceRegistry
        fields = (
            'key',
            'name',
            'description',
            'url',
            # 'query_url',
            'query_type',
            'result_regex',
            'time_to_live',
            'srid',
            'layer_typename',
            'service_version',
            'provenance',
            'notes',
            'licensing',
        )
