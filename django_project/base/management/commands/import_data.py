# coding=utf-8
"""Management command to import GeoContext data from JSON file."""

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
        print('Importing GeoContext Data from %s ...' % options['file_uri'])
        # Check if back up is needed
        delete_data()
        backup_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'backups'
        )
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        backup_file = os.path.join(
            backup_dir,
            'geocontext_backup_%s.json' % datetime.now().strftime(
                '%Y%m%d_%H%M%S')
        )
        export_data(backup_file)
        print('Previous GeoContext data is backup-ed at %s' % backup_file)

        import_data(options['file_uri'])
