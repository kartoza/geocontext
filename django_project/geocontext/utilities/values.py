from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.utilities.service import async_retrieve_service, ServiceUtil
from geocontext.utilities.cache import create_cache, retrieve_cache


class GroupValues(object):
    """Class for holding values of context group to be serialized."""
    def __init__(self, x: str, y: str, group_key: str,
                 srid: int = 4326, dist: float = 10.0):
        self.x = x
        self.y = y
        self.srid = srid
        self.dist = dist
        self.group = Group.objects.get(key=group_key)
        self.key = self.group.key
        self.name = self.group.name
        self.graphable = self.group.graphable
        self.service_registry_values = []  # TODO Rename to 'service_values'

    def populate_group_values(self):
        """Populate GroupValue with service values.
        First identify values not in cache.
        Then fetch all external values using threaded ServiceUtil.
        Finally add new values to cache and to instance to serialize
        Ensures ORM is not touched during async network data request
        """
        service_utils = []
        group_services = GroupServices.objects.filter(group=self.group).order_by('order')
        for group_service in group_services:
            # Init ServiceUtil and check if it is in cache
            service_util = ServiceUtil(
                group_service.service.key, self.x, self.y, self.srid, self.dist)
            cache = retrieve_cache(service_util)

            # Append all the caches found locally - add session and list values not found
            if cache is None:
                service_utils.append(service_util)
            else:
                self.service_registry_values.append(cache)

        # Parallel request external resources not found locally and add to cache
        if len(service_utils) > 0:
            # Async external requests
            new_service_utils = async_retrieve_service(service_utils)

            # Add new values to cache
            for new_service_util in new_service_utils:
                cache = create_cache(new_service_util.service_util)
                self.service_registry_values.append(cache)


class CollectionValues(GroupValues):
    """Class for holding values of collection of group values to be serialized."""
    def __init__(self, x: str, y: str, collection_key: str,
                 srid: int = 4326, dist: float = 10.0):
        """Initialize method for context collection value."""
        self.x = x
        self.y = y
        self.srid = srid
        self.dist = dist
        self.collection = Collection.objects.get(key=collection_key)
        self.key = self.collection.key
        self.name = self.collection.name
        self.context_group_values = []  # I would like to rename to 'group_values'

    def populate_collection_values(self):
        """Populate CollectionValue with service values.
        First identify values not in cache.
        Then fetch all external values using threaded ServiceUtil.
        Finally add new values to cache and add these to a list of group instances
        to serialize. Ensures ORM is not touched during async network data request
        """
        service_utils = []
        group_caches = {}
        collection_groups = CollectionGroups.objects.filter(
                                collection=self.collection).order_by('order')

        # We need to find CRS not in cache in all groups
        for collection_group in collection_groups:
            group = Group.objects.get(key=collection_group.group.key)
            group_services = GroupServices.objects.filter(group=group).order_by('order')
            for group_service in group_services:
                # Init ServiceUtil and check if it is in cache
                service_util = ServiceUtil(
                    group_service.service.key, self.x, self.y, self.srid, self.dist)
                cache = retrieve_cache(service_util)

                # Append all the caches found locally - list still needed
                if cache is None:
                    service_util.group_key = group.key
                    service_utils.append(service_util)
                else:
                    if group.key in group_caches:
                        group_caches[group.key].append(cache)
                    else:
                        group_caches[group.key] = [cache]

        if len(service_utils) > 0:
            # Async external requests
            new_service_utils = async_retrieve_service(service_utils)

            for new_service_util in new_service_utils:
                # Add new values to cache
                cache = create_cache(new_service_util.service_util)
                if new_service_util.group_key in group_caches:
                    group_caches[new_service_util.group_key].append(cache)
                else:
                    group_caches[new_service_util.group_key] = [cache]

        # Init contextgroup add GroupValues to be serialized
        for group_key, cache_list in group_caches.items():
            group_values = GroupValues(self.x, self.y, group_key, self.srid, self.dist)
            for cache in cache_list:
                group_values.service_registry_values.append(cache)
            self.context_group_values.append(group_values)
