import os
from datetime import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from .utilities import import_data, import_v1_data, export_data, delete_data


logger = logging.getLogger(__name__)


default_file_uri = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'geocontext.json')


class Command(BaseCommand):
    """Import GeoContext data."""
    help = 'Import GeoContext data'

    def add_arguments(self, parser):
        parser.add_argument('--file_uri', dest='file_uri', default=default_file_uri)
        parser.add_argument('--v1', dest='v1', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        logger.info(f"Importing GeoContext Data from {options['file_uri']} ...")       
        backup_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        date = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'geocontext_backup_{date}.json')
        export_data(backup_file)
        logger.info(f'Previous GeoContext data is backed up at {backup_file}')
        delete_data()
        if options['v1']:
            import_v1_data(options['file_uri'])
        else:
            import_data(options['file_uri'])
