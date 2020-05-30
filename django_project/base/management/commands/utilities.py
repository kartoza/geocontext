import os
import json
import requests

from django.core.exceptions import ValidationError

from geocontext.models.csr import ContextServiceRegistry
from geocontext.models.roup import ContextGroup
from geocontext.models.collection import ContextCollection
from geocontext.models.group_services import ContextGroupServices
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.csr import ContextServiceRegistrySerializer
from geocontext.serializers.group import ContextGroupSerializer
from geocontext.serializers.collection import ContextCollectionSerializer


def export_data(file_path):
    """Export context service data to file_path as json file.

    :param file_path: Path to json file.
    :type file_path: str
    """
    # Context Service Registries
    csr_list = ContextServiceRegistry.objects.all()
    csr_serializer = ContextServiceRegistrySerializer(csr_list, many=True)

    # Context Groups
    groups = ContextGroup.objects.all()
    group_serializer = ContextGroupSerializer(groups, many=True)

    # Context Collection
    collections = ContextCollection.objects.all()
    collection_serializer = ContextCollectionSerializer(collections, many=True)

    # Aggregate Data
    data = {
        'context_service_registry': csr_serializer.data,
        'context_group': group_serializer.data,
        'context_collection': collection_serializer.data
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
        with open(file_uri) as f:
            data = json.load(f)
    else:
        r = requests.get(file_uri)
        data = r.json()

    # Load Context Service Registries
    csr_list = data['context_service_registry']
    for csr_data in csr_list:
        service_registry, created = ContextServiceRegistry.objects. \
            get_or_create(key=csr_data['key'])
        # Change to load from dictionary
        for k, v in csr_data.items():
            setattr(service_registry, k, v)
        service_registry.save()

        try:
            service_registry.full_clean()
            service_registry.save()
        except ValidationError as e:
            print(f'   >>> CSR {service_registry.name} is not clean because {e} ')
            service_registry.delete()

    # Load Context Groups
    groups = data['context_group']
    for group_data in groups:
        group, created = ContextGroup.objects. \
            get_or_create(key=group_data['key'])
        # Change to load from dictionary
        for k, v in group_data.items():
            if k == 'context_service_registry_keys':
                csr_keys = v
                i = 0
                for csr_key in csr_keys:
                    try:
                        csr = ContextServiceRegistry.objects.get(key=csr_key)
                    except ContextServiceRegistry.DoesNotExist:
                        print(f'No CSR registered for {csr_key}')
                        continue

                    group_service = ContextGroupServices(
                        context_group=group,
                        context_service_registry=csr,
                        order=i
                    )
                    group_service.save()
                    i += 1
            setattr(group, k, v)
        try:
            group.full_clean()
            group.save()
        except ValidationError as e:
            print(f'   >>> Context Group {group.name} is not clean because {e} ')
            group.delete()

    # Load Context Collections
    collections = data['context_collection']
    for collection_data in collections:
        collection, created = ContextCollection.objects. \
            get_or_create(key=collection_data['key'])
        # Change to load from dictionary
        for k, v in collection_data.items():
            if k == 'context_group_keys':
                group_keys = v
                i = 0
                for group_key in group_keys:
                    group = ContextGroup.objects.get(
                        key=group_key)
                    collection_group = CollectionGroups(
                        context_collection=collection,
                        context_group=group,
                        order=i
                    )
                    collection_group.save()
                    i += 1
            setattr(collection, k, v)
        try:
            collection.full_clean()
            collection.save()
        except ValidationError as e:
            print(f'   >>> Context Collection {collection.name}'
                  f' is not clean because: {e} '
                  )
            collection.delete()

    print('After import data process...')
    print(f'   Number of CSR {ContextServiceRegistry.objects.count()}')
    print(f'   Number of Context Group {ContextGroup.objects.count()}')
    print(f'   Number of Context Collection {ContextCollection.objects.count()}')


def delete_data():
    """Delete geocontext data utilities method."""
    print('Before delete process...')
    print(f'   Number of CSR {ContextServiceRegistry.objects.count()}')
    print(f'   Number of Context Group {ContextGroup.objects.count()}')
    print(f'   Number of Context Collection {ContextCollection.objects.count()}')

    csr_list = ContextServiceRegistry.objects.all()
    for csr in csr_list:
        csr.delete()

    groups = ContextGroup.objects.all()
    for group in groups:
        group.delete()

    collections = ContextCollection.objects.all()
    for collection in collections:
        collection.delete()

    print('After delete process...')
    print(f'   Number of CSR {ContextServiceRegistry.objects.count()}')
    print(f'   Number of Context Group {ContextGroup.objects.count()}')
    print(f'   Number of Context Collection {ContextCollection.objects.count()}')
