from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from geocontext.models.context_cache import ContextCache


class ContextValueSerializer(serializers.ModelSerializer):
    """JSON serializer for context cache.."""

    key = serializers.ReadOnlyField(source='service_registry.key')
    name = serializers.ReadOnlyField(
        source='service_registry.name')
    description = serializers.ReadOnlyField(
        source='service_registry.description')
    query_type = serializers.ReadOnlyField(
        source='service_registry.query_type')

    class Meta:
        model = ContextCache
        fields = (
            'key',
            'value',
            'name',
            'description',
            'query_type',
        )


class ContextValueGeoJSONSerializer(
    ContextValueSerializer, GeoFeatureModelSerializer):
    """Geo JSON serializer for context cache.."""

    # I am not sure why I need to do this to make it work.
    geometry = GeometrySerializerMethodField()

    def get_geometry(self, obj):
        return obj.geometry

    class Meta(ContextValueSerializer.Meta):
        geo_field = 'geometry'
