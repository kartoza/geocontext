from django.core.management.base import BaseCommand
import logging

from geocontext.models.cache import ContextCache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to delete all context cache."""

    help = 'Delete context cache'

    def handle(self, *args, **options):
        caches = ContextCache.objects.all()
        num_caches = ContextCache.objects.all().count()
        print(f'Deleting  cache')
        for cache in caches:
            cache.delete()
            print('.')
        print(f'{num_caches} cache deleted')
        num_caches = ContextCache.objects.all().count()
        print('Current number of caches: {num_caches}')
