import os

from django.core.management.base import BaseCommand
import logging

from .utilities import export_data


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Export GeoContext data."""

    help = 'Export GeoContext data'

    def handle(self, *args, **options):
        print('Exporting GeoContext Data...')
        geocontext_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'geocontext.json'
        )

        export_data(geocontext_file)

        print('Export GeoContext data finished...')
