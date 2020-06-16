from datetime import datetime
import logging
import pytz

from django.core.management.base import BaseCommand

from geocontext.models.cache import Cache

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to delete expired caches to be run as cron."""

    help = 'Delete expired caches'

    def handle(self, *args, **options):
        num_caches = Cache.objects.all().count()
        logger.info(f'Deleting  cache')
        current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        Cache.objects.filter(expired_time__lte=current_time).delete()
        logger.info(f'{num_caches} cache deleted')
        num_caches = Cache.objects.all().count()
        logger.info('Current number of caches: {num_caches}')
