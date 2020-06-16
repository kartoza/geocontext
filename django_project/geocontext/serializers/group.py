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
            'service_keys',
        )

    def get_service_keys(self, obj) -> list:
        group_services = GroupServices.objects.filter(group=obj).order_by('order')
        return [group_service.service.key for group_service in group_services]


class GroupValueSerializer(serializers.Serializer):
    """Serializer for Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    service_values = serializers.ListSerializer(child=CacheSerializer())
