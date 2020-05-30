from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_cache import ContextCache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to delete all context cache."""

    help = 'Delete context cache'

    def handle(self, *args, **options):
        context_caches = ContextCache.objects.all()
        num_context_caches = ContextCache.objects.all().count()
        print(f'Deleting  cache')
        for context_cache in context_caches:
            context_cache.delete()
            print('.')
        print(f'{num_context_caches} cache deleted')
        num_context_caches = ContextCache.objects.all().count()
        print('Current number of caches: {num_context_caches}')
