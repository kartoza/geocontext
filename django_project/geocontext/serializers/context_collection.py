# coding=utf-8
"""Serializer for context collection."""

from concurrent.futures import ThreadPoolExecutor

from django.shortcuts import get_object_or_404

from rest_framework import serializers
from geocontext.models.context_collection import ContextCollection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.context_group import (
    ContextGroupValue, ContextGroupValueSerializer)


class ContextCollectionSerializer(serializers.ModelSerializer):
    """Serializer class for Context Collection."""

    context_group_keys = serializers.SerializerMethodField(
        source='context_groups.key')

    class Meta:
        model = ContextCollection
        fields = (
            'key',
            'name',
            'description',
            'context_group_keys',
        )

    def get_context_group_keys(self, obj):
        keys = []
        collection_groups = CollectionGroups.objects.filter(
            context_collection=obj).order_by('order')
        for collection_group in collection_groups:
            keys.append(collection_group.context_group.key)

        return keys


class ContextCollectionValue(object):
    """Class for holding values of context collection."""

    def __init__(self, x, y, context_collection_key, srid=4326):
        """Initialize method for context collection value."""
        self.x = x
        self.y = y
        self.context_collection = get_object_or_404(
            ContextCollection, key=context_collection_key)
        self.key = self.context_collection.key
        self.name = self.context_collection.name
        self.srid = srid
        self.context_group_values = []

        self.populate_context_group_values()

    # TODO first query the cache before threading

    def populate_context_group_values(self):
        """Populate context group values."""
        self.context_group_values = []
        col_groups = CollectionGroups.objects.filter(
            context_collection=self.context_collection).order_by('order')

        with ThreadPoolExecutor() as executor:
            for result in executor.map(self.retrieve_groups, col_groups):
                self.context_group_values.append(result)

    def retrieve_groups(self, collection_group):
        group_key = collection_group.context_group.key
        group_value = ContextGroupValue(self.x, self.y, group_key, self.srid)
        return group_value

    # TODO Now we need to insert into the cache again since retrieve_context_value doesnt

class ContextCollectionValueSerializer(serializers.Serializer):
    """Serializer for Context Collection Value class."""
    key = serializers.CharField()
    name = serializers.CharField()
    context_group_values = serializers.ListSerializer(
        child=ContextGroupValueSerializer())
