# coding=utf-8
"""Management command to delete all data."""

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Delete GeoContext data."""

    help = 'Export GeoContext data'

    def handle(self, *args, **options):
        print('Deleting GeoContext Data...')

        print('Before delete process...')
        print('Number of CSR %s' % ContextServiceRegistry.objects.count())
        print('Number of Context Group %s' % ContextGroup.objects.count())
        print('Number of Context Collection %s' %
              ContextCollection.objects.count())

        context_service_registries = ContextServiceRegistry.objects.all()
        for context_service_registry in context_service_registries:
            context_service_registry.delete()

        context_groups = ContextGroup.objects.all()
        for context_group in context_groups:
            context_group.delete()

        context_collections = ContextCollection.objects.all()
        for context_collection in context_collections:
            context_collection.delete()

        print('After delete process...')
        print('Number of CSR %s' % ContextServiceRegistry.objects.count())
        print('Number of Context Group %s' % ContextGroup.objects.count())
        print('Number of Context Collection %s' %
              ContextCollection.objects.count())
