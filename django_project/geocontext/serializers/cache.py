from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer,
    GeometrySerializerMethodField
)

from geocontext.models.cache import Cache


class CacheSerializer(serializers.ModelSerializer):
    """JSON serializer for cache."""
    key = serializers.ReadOnlyField(source='service.key')
    name = serializers.ReadOnlyField(source='service.name')
    description = serializers.ReadOnlyField(source='service.description')
    query_type = serializers.ReadOnlyField(source='service.query_type')

    class Meta:
        model = Cache
        fields = (
            'key',
            'value',
            'name',
            'description',
            'query_type',
        )


class CacheGeoJSONSerializer(CacheSerializer, GeoFeatureModelSerializer):
    """GeoJSON serializer for cache."""
    geometry = GeometrySerializerMethodField()

    def get_geometry(self, obj):
        return obj.geometry

    class Meta(CacheSerializer.Meta):
        geo_field = 'geometry'
