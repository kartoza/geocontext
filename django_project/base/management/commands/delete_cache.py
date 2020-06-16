from django.core.management.base import BaseCommand
import logging

from geocontext.models.cache import Cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to delete all caches."""

    help = 'Delete cache'

    def handle(self, *args, **options):
        caches = Cache.objects.all()
        num_caches = Cache.objects.all().count()
        logger.info(f'Deleting cache')
        for cache in caches:
            cache.delete()
            logger.info('.')
        logger.info(f'{num_caches} cache deleted')
        num_caches = Cache.objects.all().count()
        logger.info('Current number of caches: {num_caches}')
