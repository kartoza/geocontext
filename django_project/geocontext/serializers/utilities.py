from django.shortcuts import get_object_or_404

from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.models.collection import Collection
from geocontext.models.utilities import (
    CSRUtils,
    thread_retrieve_external,
    UtilArg
)


class GroupValues(object):
    """Class for holding values of context group."""
    def __init__(self, x, y, group_key, srid):
        self.group = get_object_or_404(Group, key=group_key)
        self.x = x
        self.y = y
        self.srid = srid
        self.key = self.group.key
        self.name = self.group.name
        self.graphable = self.group.graphable
        self.csr_values = []

    def populate_group_values(self):
        """Populate GroupValue with service registry values.
        First identify values not in cache.
        Then fetch all external values using threaded CSRUtil.
        Finally add new values to cache.
        Ensures ORM is not touched during threading
        """
        util_arg_list = []
        group_services = GroupServices.objects.filter(group=self.group).order_by('order')
        for group_service in group_services:
            csr_util = CSRUtils(group_service.csr.key, self.x, self.y, self.srid)
            cache = csr_util.retrieve_cache()

            # Append all the caches found locally - list still needed
            if cache is None:
                util_arg = UtilArg(group_key=None, csr_util=csr_util)
                util_arg_list.append(util_arg)
            else:
                self.csr_values.append(cache)

        # Parallel request external resources not found locally
        if len(util_arg_list) > 0:
            new_util_arg_list = thread_retrieve_external(util_arg_list)

            # Add new external resources to cache
            for new_util_arg in new_util_arg_list:
                if new_util_arg is not None:
                    self.csr_values.append(new_util_arg.csr_util.create_cache())


class CollectionValues(GroupValues):
    """Class for holding values of collection of group values."""
    def __init__(self, x, y, collection_key, srid):
        """Initialize method for context collection value."""
        self.x = x
        self.y = y
        self.srid = srid
        self.collection = get_object_or_404(Collection, key=collection_key)
        self.key = self.collection.key
        self.name = self.collection.name
        self.group_values = []

    def populate_collection_values(self):
        """Populate CollectionValue with service registry values.
        First identify values not in cache.
        Then fetch all external values using threaded CSRUtil.
        Finally add new values to cache.
        Ensures ORM is not touched during threading
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
                csr_util = CSRUtils(group_service.csr.key, self.x, self.y, self.srid)
                cache = csr_util.retrieve_cache()

                # Append all the caches found locally - list still needed
                if cache is None:
                    util_arg = UtilArg(group_key=group.key, csr_util=csr_util)
                    util_arg_list.append(util_arg)
                else:
                    if group.key in group_caches:
                        group_caches[group.key].append(cache)
                    else:
                        group_caches[group.key] = [cache]

        # Parallel request external resources not found locally
        if len(util_arg_list) > 0:
            new_util_arg_list = thread_retrieve_external(util_arg_list)

            # Add new external resources to dict with group: [cache]
            for new_util_arg in new_util_arg_list:
                if new_util_arg is not None:
                    cache = new_util_arg.csr_util.create_cache()
                    if new_util_arg.group_key in group_caches:
                        group_caches[new_util_arg.group_key].append(cache)
                    else:
                        group_caches[new_util_arg.group_key] = [cache]

        # Init contextgroup parent and add group key
        for group_key, cache_list in group_caches.items():
            group_values = GroupValues(self.x, self.y, group_key, self.srid)
            for cache in cache_list:
                group_values.csr_values.append(cache)
            self.group_values.append(group_values)
