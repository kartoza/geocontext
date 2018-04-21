# coding=utf-8
"""Management command to load service registry data."""

import os
import json

from django.core.management.base import BaseCommand
import logging

from geocontext.models.context_service_registry import ContextServiceRegistry

logger = logging.getLogger(__name__)


def is_attribute_complete(service_registry):
    """Check if the service registry has complete attributes.

    :param service_registry: Dictionary of attributes.
    :type service_registry: dict

    :return: True if complete, else False.
    :rtype: bool
    """
    expected_keys = [
        'key',
        'display_name',
        'url',
        'layer_typename',
        'query_type',
        'srid',
        'result_regex',
        'service_version'
    ]
    for expected_key in expected_keys:
        if expected_key not in service_registry.keys():
            return False
    return True


class Command(BaseCommand):
    """Load service registry data."""

    help = 'Load service registry data'

    def handle(self, *args, **options):
        service_registry_data_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'service_registry_data.json'
        )
        if os.path.exists(service_registry_data_file):
            print('File %s found, continue' % service_registry_data_file)
        else:
            print('File %s not found, abort.' % service_registry_data_file)
        data = json.load(open(service_registry_data_file))
        loaded = 0
        failed_load = 0
        incomplete_item = 0
        total_data = 0
        for service_registry_data in data:
            total_data += 1
            if is_attribute_complete(service_registry_data):
                print('Creating/Updating %s' % service_registry_data['key'])
                service_registry, created = ContextServiceRegistry.objects.\
                    get_or_create(key=service_registry_data['key'])
                for k, v in service_registry_data.items():
                    setattr(service_registry, k, v)
                service_registry.save()
                if service_registry:
                    loaded += 1
                    print(
                        '...Successfully create/update %s' %
                        service_registry.key)
                else:
                    failed_load += 1
            else:
                incomplete_item += 1
        print('Total data: %d item' % total_data)
        print('Incomplete items: %d item' % incomplete_item)
        print('Success loading : %d item' % loaded)
        print('Failed loading : %d item' % failed_load)
