from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.auth.admin import (
    UserAdmin as BaseUserAdmin
)
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe

from geocontext.models import UserProfile, UserTier
from geocontext.models.cache import Cache
from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.service import Service
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices


class GroupServicesInLine(admin.TabularInline):
    """Inline Admin for GroupServices"""
    model = GroupServices
    sortable_field_name = 'order'
    ordering = ('order',)
    extra = 0


class CollectionGroupsInLine(admin.TabularInline):
    """Inline Admin for CollectionGroups"""
    model = CollectionGroups
    sortable_field_name = 'order'
    ordering = ('order',)
    extra = 0


class ServiceAdmin(admin.ModelAdmin):
    """Service admin model."""
    list_display = ('key', 'name', 'query_type', 'url', 'groups')
    search_fields = ('key', 'name')

    def groups(self, service):
        groups = Group.objects.filter(services=service)
        html = ''
        for group in groups:
            html += '<li><a href="{}">{}</a></li>'.format(
                reverse("admin:geocontext_group_change", args=(group.pk,)),
                group.key
            )
        return mark_safe('<ul style="list-style-type:none">{}</ul>'.format(html))


class CacheAdmin(OSMGeoAdmin):
    """Cache admin model."""
    list_display = ('name', 'service', 'value', 'expired_time')


class GroupAdmin(admin.ModelAdmin):
    """Group admin model."""
    list_display = ('key', 'name', 'group_type', 'description')
    search_fields = ('key', 'name')
    inlines = [GroupServicesInLine]


class CollectionAdmin(admin.ModelAdmin):
    """Collection admin model."""
    list_display = ('key', 'name', 'description')
    search_fields = ('key', 'name')
    inlines = [CollectionGroupsInLine]


class UserProfileInline(admin.StackedInline):
    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Additional Information'


class UserTierAdmin(admin.ModelAdmin):
    list_display = (
        'order', 'name', 'price_amount'
    )


class UserAdmin(BaseUserAdmin):
    inlines = (
        UserProfileInline,
    )
    list_display = (
        'username',
        'email',
        'tier'
    )

    def tier(self, obj):
        user_tier = obj.user_profile.user_tier
        return user_tier.name if user_tier else '-'


admin.site.register(Service, ServiceAdmin)
admin.site.register(Cache, CacheAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Collection, CollectionAdmin)

admin.site.register(UserTier, UserTierAdmin)
# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
