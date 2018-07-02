# coding=utf-8
"""Management command to delete all data."""

from django.core.management.base import BaseCommand
import logging
from .utilities import delete_data

logger = logging.getLogger(__name__)



class Command(BaseCommand):
    """Delete GeoContext data."""

    help = 'Export GeoContext data'

    def handle(self, *args, **options):
        print('Deleting GeoContext Data...')

        delete_data()
