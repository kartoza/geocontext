import os
import json
import requests

from django.core.exceptions import ValidationError

from geocontext.models.csr import CSR
from geocontext.models.roup import Group
from geocontext.models.collection import Collection
from geocontext.models.group_services import GroupServices
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.csr import CSRSerializer
from geocontext.serializers.group import GroupSerializer
from geocontext.serializers.collection import CollectionSerializer


def export_data(file_path):
    """Export context service data to file_path as json file.

    :param file_path: Path to json file.
    :type file_path: str
    """
    # Context Service Registries
    csr_list = CSR.objects.all()
    csr_serializer = CSRSerializer(csr_list, many=True)

    # Context Groups
    groups = Group.objects.all()
    group_serializer = GroupSerializer(groups, many=True)

    # Context Collection
    collections = Collection.objects.all()
    collection_serializer = CollectionSerializer(collections, many=True)

    # Aggregate Data
    data = {
        'csr': csr_serializer.data,
        'group': group_serializer.data,
        'collection': collection_serializer.data
    }

    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)


def import_data(file_uri):
    """Import context service data from file_path.

    :param file_uri: Path to json resource.
    :type file_uri: str
    """
    # Read json file
    if os.path.exists(file_uri):
        with open(file_uri) as f:
            data = json.load(f)
    else:
        r = requests.get(file_uri)
        data = r.json()

    # Load Context Service Registries
    csr_list = data['csr']
    for csr_data in csr_list:
        csr, created = CSR.objects.get_or_create(key=csr_data['key'])
        # Change to load from dictionary
        for k, v in csr_data.items():
            setattr(csr, k, v)
        csr.save()

        try:
            csr.full_clean()
            csr.save()
        except ValidationError as e:
            print(f'   >>> CSR {csr.name} is not clean because {e} ')
            csr.delete()

    # Load Context Groups
    groups = data['group']
    for group_data in groups:
        group, created = Group.objects. \
            get_or_create(key=group_data['key'])
        # Change to load from dictionary
        for k, v in group_data.items():
            if k == 'csr_keys':
                csr_keys = v
                i = 0
                for csr_key in csr_keys:
                    try:
                        csr = CSR.objects.get(key=csr_key)
                    except CSR.DoesNotExist:
                        print(f'No CSR registered for {csr_key}')
                        continue

                    group_service = GroupServices(group=group, csr=csr, order=i)
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
    collections = data['collection']
    for collection_data in collections:
        collection, created = Collection.objects.get_or_create(key=collection_data['key'])
        # Change to load from dictionary
        for k, v in collection_data.items():
            if k == 'group_keys':
                group_keys = v
                i = 0
                for group_key in group_keys:
                    group = Group.objects.get(key=group_key)
                    collection_group = CollectionGroups(
                        collection=collection,
                        group=group,
                        order=i
                    )
                    collection_group.save()
                    i += 1
            setattr(collection, k, v)
        try:
            collection.full_clean()
            collection.save()
        except ValidationError as e:
            print(f'   >>> Collection {collection.name} is not clean because: {e}')
            collection.delete()

    print('After import data process...')
    print(f'   Number of CSR {CSR.objects.count()}')
    print(f'   Number of Group {Group.objects.count()}')
    print(f'   Number of Collection {Collection.objects.count()}')


def delete_data():
    """Delete geocontext data utilities method."""
    print('Before delete process...')
    print(f'   Number of CSR {CSR.objects.count()}')
    print(f'   Number of Group {Group.objects.count()}')
    print(f'   Number of Collection {Collection.objects.count()}')

    csr_list = CSR.objects.all()
    for csr in csr_list:
        csr.delete()

    groups = Group.objects.all()
    for group in groups:
        group.delete()

    collections = Collection.objects.all()
    for collection in collections:
        collection.delete()

    print('After delete process...')
    print(f'   Number of CSR {CSR.objects.count()}')
    print(f'   Number of Group {Group.objects.count()}')
    print(f'   Number of Collection {Collection.objects.count()}')
