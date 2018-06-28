# coding=utf-8
"""Management command to export GeoContext data to JSON file."""

import os
import json

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer
)
from geocontext.serializers.context_group import ContextGroupSerializer
from geocontext.serializers.context_collection import (
    ContextCollectionSerializer
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

        # Context Service Registries
        context_service_registries = ContextServiceRegistry.objects.all()
        csr_serializer = ContextServiceRegistrySerializer(
            context_service_registries, many=True)

        # Context Groups
        context_groups = ContextGroup.objects.all()
        context_group_serializer = ContextGroupSerializer(
            context_groups, many=True)

        # Context Collection
        context_collections = ContextCollection.objects.all()
        context_collection_serializer = ContextCollectionSerializer(
            context_collections, many=True)

        # Aggregate Data
        data = {
            'context_service_registry': csr_serializer.data,
            'context_group': context_group_serializer.data,
            'context_collection': context_collection_serializer.data
        }

        with open(geocontext_file, 'w') as outfile:
            json.dump(
                data,
                outfile,
                indent=4,
                ensure_ascii=False)
        print('Export GeoContext data finished...')
