"""Model admin class definitions."""

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from geocontext.models.csr import CSR
from geocontext.models.cache import Cache
from geocontext.models.group import Group
from geocontext.models.collection import Collection
from geocontext.models.group_services import GroupServices
from geocontext.models.collection_groups import CollectionGroups


class GroupServicesInLine(admin.TabularInline):
    """Inline Admin for GroupServices"""
    model = GroupServices
    sortable_field_name = 'order'
    ordering = ('order', )
    extra = 0


class CollectionGroupsInLine(admin.TabularInline):
    """Inline Admin for CollectionGroups"""
    model = CollectionGroups
    sortable_field_name = 'order'
    ordering = ('order',)
    extra = 0


class CSRAdmin(admin.ModelAdmin):
    """Context Service Registry admin model."""
    list_display = ('key', 'name', 'query_type', 'url')


class CacheAdmin(OSMGeoAdmin):
    """Context Cache admin model."""
    list_display = ('name', 'service_registry', 'value', 'expired_time')


class GroupAdmin(admin.ModelAdmin):
    """Context Group admin model."""
    list_display = ('key', 'name', 'group_type', 'description')
    inlines = [GroupServicesInLine]


class CollectionAdmin(admin.ModelAdmin):
    """Context Collection admin model."""
    list_display = ('key', 'name', 'description')
    inlines = [CollectionGroupsInLine]


admin.site.register(CSR, CSRAdmin)
admin.site.register(Cache, CacheAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Collection, CollectionAdmin)
