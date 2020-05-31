from rest_framework import serializers

from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.group import GroupValueSerializer


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer class for Context Collection."""
    group_keys = serializers.SerializerMethodField(source='groups.key')

    class Meta:
        model = Collection
        fields = (
            'key',
            'name',
            'description',
            'group_keys',
        )

    def get_group_keys(self, obj):
        keys = []
        collection_groups = CollectionGroups.objects.filter(
                                collection=obj).order_by('order')
        for collection_group in collection_groups:
            keys.append(collection_group.group.key)
        return keys


class CollectionValueSerializer(serializers.Serializer):
    """Serializer for Collection Value class."""
    key = serializers.CharField()
    name = serializers.CharField()
    group_values = serializers.ListSerializer(child=GroupValueSerializer())
