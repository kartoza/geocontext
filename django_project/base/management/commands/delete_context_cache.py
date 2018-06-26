# coding=utf-8
"""Management command to delete all context cache."""

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_cache import ContextCache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Load service registry data."""

    help = 'Delete context cache'

    def handle(self, *args, **options):
        context_caches = ContextCache.objects.all()
        num_context_caches = ContextCache.objects.all().count()
        print('Deleting %d cache' % num_context_caches)
        for context_cache in context_caches:
            context_cache.delete()
            print('.')
        print('%d cache deleted' % num_context_caches)
        num_context_caches = ContextCache.objects.all().count()
        print('Current number of caches: %d' % num_context_caches)
