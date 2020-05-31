from rest_framework import serializers

from geocontext.models.group import Group
from geocontext.serializers.cache import CacheValueSerializer


class GroupSerializer(serializers.ModelSerializer):
    """Serializer class for Group."""
    csr_keys = serializers.SerializerMethodField(source='csr.key')

    class Meta:
        model = Group
        fields = (
            'key',
            'name',
            'description',
            'graphable',
            'csr_keys',

        )


class GroupValueSerializer(serializers.Serializer):
    """Serializer for Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    csr_values = serializers.ListSerializer(child=CacheValueSerializer())
