# coding=utf-8
"""Utilities for commands."""

import os
import json
import requests

from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_group import ContextGroup
from geocontext.models.context_collection import ContextCollection

from geocontext.models.context_group_services import ContextGroupServices
from geocontext.models.collection_groups import CollectionGroups

from geocontext.serializers.context_service_registry import (
    ContextServiceRegistrySerializer)
from geocontext.serializers.context_group import ContextGroupSerializer
from geocontext.serializers.context_collection import (
    ContextCollectionSerializer)


def export_data(file_path):
    """Export context service data to file_path as json file.

    :param file_path: Path to json file.
    :type file_path: str
    """
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

    with open(file_path, 'w') as outfile:
        json.dump(
            data,
            outfile,
            indent=4,
            ensure_ascii=False)


def import_data(file_uri):
    """Import context service data from file_path.

    :param file_uri: Path to json resource.
    :type file_uri: str
    """
    print('=========================')
    # Read json file
    if os.path.exists(file_uri):
        print('Read from local file')
        with open(file_uri) as f:
            data = json.load(f)
    else:
        print('Read from URL')
        r = requests.get(file_uri)
        data = r.json()

    # Load Context Service Registries
    print('Load Context Service Registry....')
    context_service_registries = data['context_service_registry']
    for csr_data in context_service_registries:
        service_registry, created = ContextServiceRegistry.objects. \
            get_or_create(key=csr_data['key'])
        # Change to load from dictionary
        for k, v in csr_data.items():
            setattr(service_registry, k, v)
        service_registry.save()
        print('   id = %s, CSR %s is loaded' % (
            service_registry.id, service_registry.name))

    # Load Context Groups
    print('Load Context Groups....')
    context_groups = data['context_group']
    for context_group_data in context_groups:
        context_group, created = ContextGroup.objects. \
            get_or_create(key=context_group_data['key'])
        # Change to load from dictionary
        for k, v in context_group_data.items():
            if k == 'context_service_registry_keys':
                context_service_registry_keys = v
                i = 0
                for csr_key in context_service_registry_keys:
                    try:
                        context_service_registry = \
                            ContextServiceRegistry.objects.get(key=csr_key)
                    except ContextServiceRegistry.DoesNotExist as e:
                        print('No CSR registered for %s' % csr_key)
                        raise e

                    context_group_service = ContextGroupServices(
                        context_group=context_group,
                        context_service_registry=context_service_registry,
                        order=i
                    )
                    context_group_service.save()
                    i += 1
            setattr(context_group, k, v)
        context_group.save()
        print('   Context Group %s is loaded' % context_group.name)

    # Load Context Collections
    print('Load Context Collection....')
    context_collections = data['context_collection']
    for context_collection_data in context_collections:
        context_collection, created = ContextCollection.objects. \
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
        print('   Context Collection %s is loaded' % context_collection.name)

    print('After import data process...')
    print('   Number of CSR %s' % ContextServiceRegistry.objects.count())
    print('   Number of Context Group %s' % ContextGroup.objects.count())
    print('   Number of Context Collection %s' %
          ContextCollection.objects.count())


def delete_data():
    """Delete geocontext data utilities method."""
    print('Before delete process...')
    print('   Number of CSR %s' % ContextServiceRegistry.objects.count())
    print('   Number of Context Group %s' % ContextGroup.objects.count())
    print('   Number of Context Collection %s' %
          ContextCollection.objects.count())

    context_service_registries = ContextServiceRegistry.objects.all()
    for context_service_registry in context_service_registries:
        context_service_registry.delete()

    context_groups = ContextGroup.objects.all()
    for context_group in context_groups:
        context_group.delete()

    context_collections = ContextCollection.objects.all()
    for context_collection in context_collections:
        context_collection.delete()

    print('After delete process...')
    print('   Number of CSR %s' % ContextServiceRegistry.objects.count())
    print('   Number of Context Group %s' % ContextGroup.objects.count())
    print('   Number of Context Collection %s' %
          ContextCollection.objects.count())
