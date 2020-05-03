# coding=utf-8
"""Serializer for context group."""

from concurrent.futures import ThreadPoolExecutor

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_group_services import ContextGroupServices
from geocontext.serializers.context_cache import ContextValueSerializer

from geocontext.models.utilities import retrieve_context


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

    def __init__(self, x, y, context_group_key, srid=4326):
        """Initialize method for context group value."""
        self.x = x
        self.y = y
        self.context_group = get_object_or_404(
            ContextGroup, key=context_group_key)
        self.key = self.context_group.key
        self.name = self.context_group.name
        self.srid = srid
        self.service_registry_values = []
        self.graphable = self.context_group.graphable
        self.populate_service_registry_values()

    def populate_service_registry_values(self):
        """Populate service registry values."""
        self.service_registry_values = []
        context_group_services = ContextGroupServices.objects.filter(
            context_group=self.context_group).order_by('order')

        with ThreadPoolExecutor() as executor:
            for result in executor.map(self.threaded_function, context_group_services):
                self.service_registry_values.append(result)          

    def threaded_function(self, context_group_service):
        registry_key = context_group_service.context_service_registry.key
        context_cache = retrieve_context(self.x, self.y, registry_key, self.srid)
        return context_cache


class ContextGroupValueSerializer(serializers.Serializer):
    """Serializer for Context Value Group class."""
    key = serializers.CharField()
    name = serializers.CharField()
    graphable = serializers.BooleanField()
    service_registry_values = serializers.ListSerializer(
        child=ContextValueSerializer())
