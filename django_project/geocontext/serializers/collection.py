from rest_framework import serializers

from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.group import GroupValueSerializer


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer class for Collection."""
    group_keys = serializers.SerializerMethodField(source='group.key')

    class Meta:
        model = Collection
        fields = (
            'key',
            'name',
            'description',
            'group_keys',
        )

    def get_group_keys(self, obj):
        groups = CollectionGroups.objects.filter(collection=obj).order_by('order')
        return [group.group.key for group in groups]


class CollectionValueSerializer(serializers.Serializer):
    """Serializer for Collection Value class."""
    key = serializers.CharField()
    name = serializers.CharField()
    context_group_values = serializers.ListSerializer(child=GroupValueSerializer())
