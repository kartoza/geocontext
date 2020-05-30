from rest_framework import serializers

from geocontext.models.group import ContextGroup
from geocontext.serializers.cache import ContextValueSerializer


class ContextGroupSerializer(serializers.ModelSerializer):
    """Serializer class for Context Group."""

    context_service_registry_keys = serializers.SerializerMethodField(
        source='service_registry.key')

    class Meta:
        model = ContextGroup
        fields = (
            'key',
            'name',
            'description',
            'graphable',
            'context_service_registry_keys',

        )


class ContextGroupValueSerializer(serializers.Serializer):
    """Serializer for Context Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(
        child=ContextValueSerializer())
