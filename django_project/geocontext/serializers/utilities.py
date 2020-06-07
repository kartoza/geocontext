from django.shortcuts import get_object_or_404

from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.models.utilities import (
    CSRUtils,
    create_cache,
    retrieve_cache,
    thread_retrieve_external,
    UtilArg
)


class GroupValues(object):
    """Class for holding values of context group to be serialized."""
    def __init__(
        self, x: str, y: str, group_key: str, srid: int = 4326, dist: float = 10.0):
        self.x = x
        self.y = y
        self.srid = srid
        self.dist = dist
        self.group = get_object_or_404(Group, key=group_key)
        self.key = self.group.key
        self.name = self.group.name
        self.graphable = self.group.graphable
        self.service_registry_values = []

    def populate_group_values(self):
        """Populate GroupValue with service registry values.
        First identify values not in cache.
        Then fetch all external values using threaded CSRUtil.
        Finally add new values to cache and to instance to serialize
        Ensures ORM is not touched during async network data request
        """
        util_arg_list = []
        group_services = GroupServices.objects.filter(group=self.group).order_by('order')
        for group_service in group_services:
            # Init CSRUtil and check if it is in cache
            csr_util = CSRUtils(
                group_service.csr.key, self.x, self.y, self.srid, self.dist)
            cache = retrieve_cache(csr_util)

            # Append all the caches found locally - list still needed
            if cache is None:
                util_arg = UtilArg(group_key=None, csr_util=csr_util)
                util_arg_list.append(util_arg)
            else:
                self.service_registry_values.append(cache)

        # Parallel request external resources not found locally and add to cache
        if len(util_arg_list) > 0:
            # Summon parallel requests for external requests
            new_util_arg_list = thread_retrieve_external(util_arg_list)

            # Add new values to cache
            for new_util_arg in new_util_arg_list:
                self.service_registry_values.append(create_cache(new_util_arg.csr_util))


class CollectionValues(GroupValues):
    """Class for holding values of collection of group values to be serialized."""
    def __init__(
        self, x: str, y: str, collection_key: str, srid: int = 4326, dist: float = 10.0):
        """Initialize method for context collection value."""
        self.x = x
        self.y = y
        self.srid = srid
        self.dist = dist
        self.collection = get_object_or_404(Collection, key=collection_key)
        self.key = self.collection.key
        self.name = self.collection.name
        self.context_group_values = []

    def populate_collection_values(self):
        """Populate CollectionValue with service registry values.
        First identify values not in cache.
        Then fetch all external values using threaded CSRUtil.
        Finally add new values to cache and add these to a list of group instances
        to serialize. Ensures ORM is not touched during async network data request
        """
        util_arg_list = []
        group_caches = {}
        collection_groups = CollectionGroups.objects.filter(
                                collection=self.collection).order_by('order')

        # We need to find CRS not in cache in all groups
        for collection_group in collection_groups:
            group = get_object_or_404(Group, key=collection_group.group.key)
            group_services = GroupServices.objects.filter(group=group).order_by('order')
            for group_service in group_services:
                # Init CSRUtil and check if it is in cache
                csr_util = CSRUtils(
                    group_service.csr.key, self.x, self.y, self.srid, self.dist)
                cache = retrieve_cache(csr_util)

                # Append all the caches found locally - list still needed
                if cache is None:
                    util_arg = UtilArg(group_key=group.key, csr_util=csr_util)
                    util_arg_list.append(util_arg)
                else:
                    if group.key in group_caches:
                        group_caches[group.key].append(cache)
                    else:
                        group_caches[group.key] = [cache]


        if len(util_arg_list) > 0:
            # Summon parallel requests for external requests
            new_util_arg_list = thread_retrieve_external(util_arg_list)

            for new_util_arg in new_util_arg_list:
                # Add new values to cache
                cache = create_cache(new_util_arg.csr_util)
                if new_util_arg.group_key in group_caches:
                    group_caches[new_util_arg.group_key].append(cache)
                else:
                    group_caches[new_util_arg.group_key] = [cache]

        # Init contextgroup add GroupValues to be serialized
        for group_key, cache_list in group_caches.items():
            group_values = GroupValues(self.x, self.y, group_key, self.srid, self.dist)
            for cache in cache_list:
                group_values.service_registry_values.append(cache)
            self.context_group_values.append(group_values)
