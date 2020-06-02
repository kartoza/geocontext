from rest_framework import serializers

from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.serializers.cache import CacheSerializer


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

    def get_csr_keys(self, obj) -> list:
        keys = []
        group_services = GroupServices.objects.filter(group=obj).order_by('order')
        for group_service in group_services:
            keys.append(group_service.csr.key)
        return keys


class GroupValueSerializer(serializers.Serializer):
    """Serializer for Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(child=CacheSerializer())
