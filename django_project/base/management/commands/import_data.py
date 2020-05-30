import os
from datetime import datetime

from django.core.management.base import BaseCommand
import logging

from .utilities import import_data, export_data, delete_data


logger = logging.getLogger(__name__)


default_file_uri = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'geocontext.json')


class Command(BaseCommand):
    """Import GeoContext data."""

    help = 'Import GeoContext data'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_uri', type=str, nargs='?', default=default_file_uri)

    def handle(self, *args, **options):
        print(f"Importing GeoContext Data from {options['file_uri']} ...")
        # Check if back up is needed
        delete_data()
        backup_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'backups'
        )
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'geocontext_backup_{date}.json')
        export_data(backup_file)
        print(f'Previous GeoContext data is backup-ed at {backup_file}')

        import_data(options['file_uri'])
