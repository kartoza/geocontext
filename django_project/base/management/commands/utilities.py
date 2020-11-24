import os
import json
import requests

from django.core.exceptions import ValidationError

from geocontext.models.service import Service
from geocontext.models.group import Group
from geocontext.models.collection import Collection
from geocontext.models.group_services import GroupServices
from geocontext.models.collection_groups import CollectionGroups
from geocontext.serializers.service import ServiceSerializer
from geocontext.serializers.group import GroupSerializer
from geocontext.serializers.collection import CollectionSerializer


def export_data(file_path):
    """Export service data to file_path as json file.

    :param file_path: Path to json file.
    :type file_path: str
    """
    services = Service.objects.all()
    service_serializer = ServiceSerializer(services, many=True)

    groups = Group.objects.all()
    group_serializer = GroupSerializer(groups, many=True)

    collections = Collection.objects.all()
    collection_serializer = CollectionSerializer(collections, many=True)

    # Aggregate Data
    data = {
        'service': service_serializer.data,
        'group': group_serializer.data,
        'collection': collection_serializer.data
    }

    with open(file_path, 'w') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)


def import_data(file_uri):
    """Import service data from file_path.

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

    # Load Services
    for service_data in data['service']:
        service, created = Service.objects.get_or_create(key=service_data['key'])
        # Change to load from dictionary
        for k, v in service_data.items():
            setattr(service, k, v)
        service.save()

        try:
            service.full_clean()
            service.save()
        except ValidationError as e:
            print(f'Service {service.name} is not clean because {e} ')
            service.delete()

    # Load Groups
    for group_data in data['group']:
        group, created = Group.objects. \
            get_or_create(key=group_data['key'])
        # Change to load from dictionary
        for k, v in group_data.items():
            if k == 'service_keys':
                service_keys = v
                i = 0
                for service_key in service_keys:
                    try:
                        service = Service.objects.get(key=service_key)
                    except Service.DoesNotExist:
                        print(f'No service registered for {service_key}')
                        continue

                    group_service = GroupServices(group=group, service=service, order=i)
                    group_service.save()
                    i += 1
            setattr(group, k, v)
        try:
            group.full_clean()
            group.save()
        except ValidationError as e:
            print(f'Group {group.name} is not clean because {e} ')
            group.delete()

    # Load Collections
    for collection_data in data['collection']:
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
            print(f'Collection {collection.name} is not clean because: {e}')
            collection.delete()

    print('After data import:')
    print(f'Service count: {Service.objects.count()}')
    print(f'Group count: {Group.objects.count()}')
    print(f'Collection count {Collection.objects.count()}')


def import_v1_data(file_uri):
    """Import service data from file_path.

    This function is aware of the Geocontext v1 service keys.
    eg. result_regex, context_service_registry_keys, context_group_keys etc.
    It also splits regex/typenames and only grabs the second part as it is all we need.

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

    # Load Services
    for service_data in data['context_service_registry']:
        service, created = Service.objects.get_or_create(key=service_data['key'])
        # Change to load from dictionary
        for k, v in service_data.items():
            if k == 'result_regex':
                k = 'layer_name'
            if k == ('result_regex' or 'layer_typename') and ':' in k:
                v = v.split(':')[-1]
            setattr(service, k, v)
        service.save()

        try:
            service.full_clean()
            service.save()
        except ValidationError as e:
            print(f'Service {service.name} is not clean because {e} ')
            service.delete()

    # Load Groups
    for group_data in data['context_group']:
        group, created = Group.objects.get_or_create(key=group_data['key'])
        # Change to load from dictionary
        for k, v in group_data.items():
            k = 'service_keys' if k == 'context_service_registry_keys' else k
            if k == 'service_keys':
                service_keys = v
                i = 0
                for service_key in service_keys:
                    try:
                        service = Service.objects.get(key=service_key)
                    except Service.DoesNotExist:
                        print(f'No service registered for {service_key}')
                        continue

                    group_service = GroupServices(group=group, service=service, order=i)
                    group_service.save()
                    i += 1
            setattr(group, k, v)
        try:
            group.full_clean()
            group.save()
        except ValidationError as e:
            print(f'Group {group.name} is not clean because {e} ')
            group.delete()

    # Load Collections
    for collection_data in data['context_collection']:
        collection, created = Collection.objects.get_or_create(key=collection_data['key'])
        # Change to load from dictionary
        for k, v in collection_data.items():
            k = 'group_keys' if k == 'context_group_keys' else k
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
            print(f'Collection {collection.name} is not clean because: {e}')
            collection.delete()

    print('After data import:')
    print(f'Service count: {Service.objects.count()}')
    print(f'Group count: {Group.objects.count()}')
    print(f'Collection count {Collection.objects.count()}')


def delete_data():
    print('Before delete:')
    print(f'Service count: {Service.objects.count()}')
    print(f'Group count: {Group.objects.count()}')
    print(f'Collection count {Collection.objects.count()}')

    services = Service.objects.all()
    for service in services:
        service.delete()

    groups = Group.objects.all()
    for group in groups:
        group.delete()

    collections = Collection.objects.all()
    for collection in collections:
        collection.delete()

    print('After deleting:')
    print(f'Service count: {Service.objects.count()}')
    print(f'Group count: {Group.objects.count()}')
    print(f'Collection count {Collection.objects.count()}')
