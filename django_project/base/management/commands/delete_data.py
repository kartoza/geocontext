import logging

from django.core.management.base import BaseCommand

from .utilities import delete_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Delete GeoContext data."""

    help = 'Export GeoContext data'

    def handle(self, *args, **options):
        logger.info('Deleting GeoContext Data...')
        delete_data()
