from django.shortcuts import get_object_or_404
from rest_framework import serializers

from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.context_group_services import ContextGroupServices
from geocontext.models.utilities import (
    CSRUtils,
    thread_retrieve_external,
    UtilArg
)
from geocontext.serializers.context_group import (
    ContextGroupValue,
    ContextGroupValueSerializer
)


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

    def populate_context_group_values(self):
        """Populate context group values."""
        self.context_group_values = []
        util_arg_list = []
        group_caches = {}
        collection_groups = CollectionGroups.objects.filter(
            context_collection=self.context_collection).order_by('order')
        for collection_group in collection_groups:
            context_group = get_object_or_404(
                ContextGroup, key=collection_group.context_group.key)
            group_services = ContextGroupServices.objects.filter(
                context_group=context_group).order_by('order')
            for group_service in group_services:
                csr_util = CSRUtils(
                    group_service.context_service_registry.key,
                    self.x,
                    self.y,
                    self.srid
                )
                cache = csr_util.retrieve_context_cache()

                # Append all the caches found locally - list still needed
                if cache is None:
                    util_arg = UtilArg(group_key=context_group.key,
                                       csr_util=csr_util)
                    util_arg_list.append(util_arg)
                else:
                    if context_group.key in group_caches:
                        group_caches[context_group.key].append(cache)
                    else:
                        group_caches[context_group.key] = [cache]

        # Parallel request external resources not found locally
        if len(util_arg_list) > 0:
            new_result_list = thread_retrieve_external(util_arg_list)

            # Add new external resources to dict with group: [cache]
            for new_util_arg in new_result_list:
                if new_util_arg is not None:
                    cache = new_util_arg.csr_util.create_context_cache()
                    if new_util_arg.group_key in group_caches:
                        group_caches[new_util_arg.group_key].append(cache)
                    else:
                        group_caches[new_util_arg.group_key] = [cache]

        # Init contextgroup serializer but override populating registry values
        for group_key, cache_list in group_caches.items():
            context_group_value = ContextGroupValue(
                self.x, self.y, group_key, self.srid, populate=False)
            for cache in cache_list:
                context_group_value.service_registry_values.append(cache)
            self.context_group_values.append(context_group_value)


class ContextCollectionValueSerializer(serializers.Serializer):
    """Serializer for Context Collection Value class."""
    key = serializers.CharField()
    name = serializers.CharField()
    context_group_values = serializers.ListSerializer(
        child=ContextGroupValueSerializer())
