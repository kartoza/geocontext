# coding=utf-8
"""Management command to import GeoContext data from JSON file."""

import os
import json

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection

from geocontext.models.context_group_services import ContextGroupServices
from geocontext.models.collection_groups import CollectionGroups

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Import GeoContext data."""

    help = 'Import GeoContext data'

    def handle(self, *args, **options):
        print('Exporting GeoContext Data...')
        geocontext_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'geocontext.json'
        )

        # Read json file
        with open(geocontext_file) as f:
            data = json.load(f)
        # print(data)
        # print(data['context_service_registry'])
        # print(data['context_group'])
        # print(data['context_collection'])

        # Load Context Service Registries
        context_service_registries = data['context_service_registry']
        for csr_data in context_service_registries:
            service_registry, created = ContextServiceRegistry.objects.\
                get_or_create(key=csr_data['key'])
            # Change to load from dictionary
            for k, v in csr_data.items():
                setattr(service_registry, k, v)
            service_registry.save()

        # Load Context Groups
        context_groups = data['context_group']
        for context_group_data in context_groups:
            context_group, created = ContextGroup.objects.\
                get_or_create(key=context_group_data['key'])
            # Change to load from dictionary
            for k, v in context_group_data.items():
                if k == 'context_service_registry_keys':
                    context_service_registry_keys = v
                    i = 0
                    for csr_key in context_service_registry_keys:
                        context_service_registry = \
                            ContextServiceRegistry.objects.get(key=csr_key)
                        context_group_service = ContextGroupServices(
                            context_group=context_group,
                            context_service_registry=context_service_registry,
                            order=i
                        )
                        context_group_service.save()
                        i += 1
                setattr(context_group, k, v)
            context_group.save()

        # Load Context Collections
        context_collections = data['context_collection']
        for context_collection_data in context_collections:
            context_collection, created = ContextCollection.objects.\
                get_or_create(key=context_collection_data['key'])
            # Change to load from dictionary
            for k, v in context_collection_data.items():
                if k == 'context_group_keys':
                    context_group_keys = v
                    i = 0
                    for context_group_key in context_group_keys:
                        context_group = ContextGroup.objects.get(
                            key=context_group_key)
                        collection_group = CollectionGroups(
                            context_collection=context_collection,
                            context_group=context_group,
                            order=i
                        )
                        collection_group.save()
                        i += 1
                setattr(context_collection, k, v)
            context_collection.save()

        print('After import data process...')
        print('Number of CSR %s' % ContextServiceRegistry.objects.count())
        print('Number of Context Group %s' % ContextGroup.objects.count())
        print('Number of Context Collection %s' %
              ContextCollection.objects.count())
