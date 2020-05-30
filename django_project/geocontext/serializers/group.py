from rest_framework import serializers

from geocontext.models.group import Group
from geocontext.serializers.cache import CacheValueSerializer


class ContextGroupSerializer(serializers.ModelSerializer):
    """Serializer class for Context Group."""

    csr_keys = serializers.SerializerMethodField(
        source='service_registry.key')

    class Meta:
        model = Group
        fields = (
            'key',
            'name',
            'description',
            'graphable',
            'csr_keys',

        )


class ContextGroupValueSerializer(serializers.Serializer):
    """Serializer for Context Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(child=CacheValueSerializer())
