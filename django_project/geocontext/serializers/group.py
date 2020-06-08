from rest_framework import serializers

from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.serializers.cache import CacheSerializer


class GroupSerializer(serializers.ModelSerializer):
    """Serializer class for Group."""
    service_keys = serializers.SerializerMethodField(source='service.key')

    class Meta:
        model = Group
        fields = (
            'key',
            'name',
            'description',
            'graphable',
            'service_keys',
        )

    def get_service_keys(self, obj) -> list:
        keys = []
        group_services = GroupServices.objects.filter(group=obj).order_by('order')
        for group_service in group_services:
            keys.append(group_service.service.key)
        return keys


class GroupValueSerializer(serializers.Serializer):
    """Serializer for Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(child=CacheSerializer())
