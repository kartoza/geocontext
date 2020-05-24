# coding=utf-8
"""Serializer for context group."""
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_group_services import ContextGroupServices
from geocontext.serializers.context_cache import ContextValueSerializer

from geocontext.models.utilities import (
    ContextServiceRegistryUtils,
    thread_retrieve_external
)


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

    def get_context_service_registry_keys(self, obj):
        keys = []
        context_group_services = ContextGroupServices.objects.filter(
            context_group=obj).order_by('order')
        for context_group_service in context_group_services:
            keys.append(context_group_service.context_service_registry.key)

        return keys


class ContextGroupValue(object):
    """Class for holding values of context group."""

    def __init__(self, x, y, context_group_key, srid=4326, populate=True):
        """Initialize method for context group value."""
        self.x = x
        self.y = y
        self.context_group = get_object_or_404(ContextGroup, key=context_group_key)
        self.key = self.context_group.key
        self.name = self.context_group.name
        self.srid = srid
        self.service_registry_values = []
        self.graphable = self.context_group.graphable

        if populate:
            self.populate_service_registry_values()

    def populate_service_registry_values(self):
        """Populate service registry values."""
        self.service_registry_values = []
        group_services = ContextGroupServices.objects.filter(
            context_group=self.context_group).order_by('order')
        external_registry_utils = []
        for group_service in group_services:
            registry_utils = ContextServiceRegistryUtils(
                group_service.context_service_registry.key, self.x, self.y, self.srid)
            cache = registry_utils.retrieve_context_cache()

            # Append all the caches found locally - list those still needed
            if cache is None:
                external_registry_utils.append((None, registry_utils))
            else:
                self.service_registry_values.append(cache)

        # Parallel request external resources not found locally
        new_result_list = thread_retrieve_external(external_registry_utils)
        
        # Add new external resources to cache
        for new_result in new_result_list:
            group_key, util = new_result[0], new_result[1]
            if util is not None:
                self.service_registry_values.append(util.create_context_cache())


class ContextGroupValueSerializer(serializers.Serializer):
    """Serializer for Context Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(
        child=ContextValueSerializer())
