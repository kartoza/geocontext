# coding=utf-8
"""Management command to export GeoContext data to JSON file."""

import os
import json

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer
)

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

        context_service_registries = ContextServiceRegistry.objects.all()
        csr_serializer = ContextServiceRegistrySerializer(
            context_service_registries, many=True)

        with open(geocontext_file, 'w') as outfile:
            json.dump(
                csr_serializer.data,
                outfile,
                indent=4,
                ensure_ascii=False)
        print('Export GeoContext data finished...')
