# coding=utf-8
"""Management command to import GeoContext data from JSON file."""

import os
from datetime import datetime

from django.core.management.base import BaseCommand
import logging

from .utilities import import_data, export_data, delete_data


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import GeoContext data."""

    help = 'Import GeoContext data'

    def handle(self, *args, **options):
        print('Importing GeoContext Data...')
        # Check if back up is needed
        if options.get('do_backup', True):
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


        geocontext_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'geocontext.json'
        )

        import_data(geocontext_file)
