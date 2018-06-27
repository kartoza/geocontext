# coding=utf-8
"""Model admin class definitions."""

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_cache import ContextCache
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection


class ContextServiceRegistryAdmin(admin.ModelAdmin):
    """Context Service Registry admin model."""
    list_display = ('key', 'display_name', 'query_type', 'parent', 'url')


class ContextCacheAdmin(OSMGeoAdmin):
    """Context Cache admin model."""
    list_display = ('name', 'service_registry', 'value', 'expired_time')


class ContextGroupAdmin(admin.ModelAdmin):
    """Context Group admin model."""
    list_display = ('key', 'name', 'description')


class ContextCollectionAdmin(admin.ModelAdmin):
    """Context Collection admin model."""
    list_display = ('key', 'name', 'description')


admin.site.register(ContextServiceRegistry, ContextServiceRegistryAdmin)
admin.site.register(ContextCache, ContextCacheAdmin)
admin.site.register(ContextGroup, ContextGroupAdmin)
admin.site.register(ContextCollection, ContextCollectionAdmin)
