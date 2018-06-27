# coding=utf-8
"""Serializer for context cache."""

from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from geocontext.models.context_cache import ContextCache


class ContextValueSerializer(serializers.ModelSerializer):
    """JSON serializer for context cache.."""

    key = serializers.ReadOnlyField(source='service_registry.key')
    parent = serializers.SerializerMethodField(
        source='service_registry.parent.key')
    display_name = serializers.ReadOnlyField(
        source='service_registry.display_name')
    description = serializers.ReadOnlyField(
        source='service_registry.description')
    query_type = serializers.ReadOnlyField(
        source='service_registry.query_type')

    class Meta:
        model = ContextCache
        fields = (
            'key',
            'parent',
            'value',
            'display_name',
            'description',
            'query_type',
        )

    def get_parent(self, obj):
        if obj.service_registry.parent:
            return obj.service_registry.parent.key
        else:
            return None


class ContextValueGeoJSONSerializer(
    ContextValueSerializer, GeoFeatureModelSerializer):
    """Geo JSON serializer for context cache.."""

    # I am not sure why I need to do this to make it work.
    geometry = GeometrySerializerMethodField()

    def get_geometry(self, obj):
        return obj.geometry

    class Meta(ContextValueSerializer.Meta):
        geo_field = 'geometry'
