# coding=utf-8
"""Serializer for context cache."""

from rest_framework import serializers
from geocontext.models.context_cache import ContextCache


class ContextCacheSerializer(serializers.ModelSerializer):
    """Serializer class for Context Service Registry."""

    key = serializers.ReadOnlyField(source='service_registry.key')

    class Meta:
        model = ContextCache
        fields = (
            'key'
            'value',
        )
