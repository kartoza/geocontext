from django.contrib.gis.geos import Point

from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.utilities.cache import create_cache, retrieve_cache
from geocontext.utilities.service import retrieve_service_value, ServiceUtil


class GroupValues(object):
    """Class for holding values of context group to be serialized."""
    def __init__(self, group_key: str, point: Point, search_dist: float):
        """Initialize method for GroupValues.

        :param collection_key: collection_key
        :type collection_key: str
        :param point: Query coordinate
        :type point: Point
        :param search_dist: Search distance query overide service.
        :type search_dist: int
        """
        self.point = point
        self.search_dist = search_dist
        self.group = Group.objects.get(key=group_key)
        self.key = self.group.key
        self.name = self.group.name
        self.service_registry_values = []  # TODO Rename to 'service_values'

    def populate_group_values(self):
        """Populate GroupValue with service values.
        First identify values not in cache.
        Then fetch all external values using async ServiceUtil.
        Finally add new values to cache and to instance to serialize
        """
        service_utils = []
        group_services = GroupServices.objects.filter(group=self.group).order_by('order')

        # Append all the caches found locally - list values not found
        for service in group_services:
            service_util = ServiceUtil(service.service.key, self.point, self.search_dist)
            cache = retrieve_cache(service_util)
            if cache is not None:
                self.service_registry_values.append(cache)
            else:
                service_utils.append(service_util)

        # Async request external resources not found locally and add to cache
        if len(service_utils) > 0:
            new_service_utils = retrieve_service_value(service_utils)
            for new_service_util in new_service_utils:
                cache = create_cache(new_service_util)
                self.service_registry_values.append(cache)
