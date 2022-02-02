import os
import logging

from django.core.management.base import BaseCommand

from .utilities import export_data


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Export GeoContext data."""

    help = 'Export GeoContext data'

    def handle(self, *args, **options):
        logger.info('Exporting GeoContext Data...')
        geocontext_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'geocontext.json'
        )
        export_data(geocontext_file)
        logger.info('Export GeoContext data finished...')
