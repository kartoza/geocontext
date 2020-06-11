from django.contrib.gis.geos import Point

from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.utilities.cache import create_cache, retrieve_cache
from geocontext.utilities.group import GroupValues
from geocontext.utilities.service import retrieve_service_value, ServiceUtil


class CollectionValues(GroupValues):
    """Class for holding values of collection of group values to be serialized."""
    def __init__(self, collection_key: str, point: Point, dist: float = 10.0):
        """Initialize method for context collection value."""
        self.point = point
        self.dist = dist
        self.collection = Collection.objects.get(key=collection_key)
        self.key = self.collection.key
        self.name = self.collection.name
        self.context_group_values = []  # TODO I would like to rename to 'group_values'

    def populate_collection_values(self):
        """Populate CollectionValue with service values.
        First identify values not in cache.
        Then fetch all external values using threaded ServiceUtil.
        Finally add new values to cache and add these to a list of group instances
        to serialize. 
        Ensures ORM is not touched during async network data requests.
        """
        service_utils = []
        group_caches = {}
        collection_groups = CollectionGroups.objects.filter(
                                collection=self.collection).order_by('order')

        # We need to find CRS not in cache in all groups
        for collection_group in collection_groups:
            group = Group.objects.get(key=collection_group.group.key)
            group_services = GroupServices.objects.filter(group=group).order_by('order')
            for service in group_services:
                # Init ServiceUtil and check if it is in cache
                service_util = ServiceUtil(service.service.key, self.point, self.dist)
                cache = retrieve_cache(service_util)

                # Append all the caches found locally per group - list still needed
                if cache is not None:
                    if group.key in group_caches:
                        group_caches[group.key].append(cache)
                    else:
                        group_caches[group.key] = [cache]
                else:
                    service_util.group_key = group.key
                    service_utils.append(service_util)

        if len(service_utils) > 0:
            # Async external requests
            new_service_utils = retrieve_service_value(service_utils)

            for new_service_util in new_service_utils:
                # Add new values to cache
                cache = create_cache(new_service_util)
                if new_service_util.group_key in group_caches:
                    group_caches[new_service_util.group_key].append(cache)
                else:
                    group_caches[new_service_util.group_key] = [cache]

        # Add GroupValues to be serialized
        for group_key, cache_list in group_caches.items():
            group_values = GroupValues(group_key, self.point, self.dist)
            for cache in cache_list:
                group_values.service_registry_values.append(cache)
            self.context_group_values.append(group_values)
