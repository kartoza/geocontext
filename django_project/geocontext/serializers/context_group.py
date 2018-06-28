# coding=utf-8
"""Serializer for context group."""

from rest_framework import serializers
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_group_services import ContextGroupServices


class ContextGroupSerializer(serializers.ModelSerializer):
    """Serializer class for Context Group."""

    context_service_registry_keys = serializers.SerializerMethodField(
        source='service_registry.parent.key')

    class Meta:
        model = ContextGroup
        fields = (
            'key',
            'name',
            'description',
            'context_service_registry_keys',
        )

    def get_context_service_registry_keys(self, obj):
        keys = []
        context_group_services = ContextGroupServices.objects.filter(
            context_group=obj).order_by('order')
        for context_group_service in context_group_services:
            keys.append(context_group_service.context_service_registry.key)

        return keys
