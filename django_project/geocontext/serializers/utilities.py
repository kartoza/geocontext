from django.shortcuts import get_object_or_404

from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.group import ContextGroup
from geocontext.models.group_services import ContextGroupServices
from geocontext.models.collection import ContextCollection
from geocontext.models.utilities import (
    CSRUtils,
    thread_retrieve_external,
    UtilArg
)


class GroupValues(object):
    """Class for holding values of context group."""
    def __init__(self, x, y, group_key, srid):
        self.group = get_object_or_404(ContextGroup, key=group_key)
        self.x = x
        self.y = y
        self.srid = srid
        self.key = self.group.key
        self.name = self.group.name
        self.graphable = self.group.graphable
        self.service_registry_values = []

    def populate_group_values(self):
        """Populate group with service registry values."""
        util_arg_list = []
        group_services = ContextGroupServices.objects.filter(
            context_group=self.group).order_by('order')
        for group_service in group_services:
            csr_util = CSRUtils(
                group_service.context_service_registry.key,
                self.x,
                self.y,
                self.srid
            )
            cache = csr_util.retrieve_cache()

            # Append all the caches found locally - list still needed
            if cache is None:
                util_arg = UtilArg(group_key=None, csr_util=csr_util)
                util_arg_list.append(util_arg)
            else:
                self.service_registry_values.append(cache)

        # Parallel request external resources not found locally
        if len(util_arg_list) > 0:
            new_result_list = thread_retrieve_external(util_arg_list)

            # Add new external resources to cache
            for new_util_arg in new_result_list:
                if new_util_arg is not None:
                    self.service_registry_values.append(
                        new_util_arg.csr_util.create_cache()
                    )


class CollectionValues(GroupValues):
    """Class for holding values of collection of group values."""
    def __init__(self, x, y, collection_key, srid):
        """Initialize method for context collection value."""
        self.x = x
        self.y = y
        self.srid = srid
        self.collection = get_object_or_404(ContextCollection, key=collection_key)
        self.key = self.collection.key
        self.name = self.collection.name
        self.group_values = []

    def populate_collection_values(self):
        """Populate context collection values."""
        util_arg_list = []
        group_caches = {}
        collection_groups = CollectionGroups.objects.filter(
            context_collection=self.collection).order_by('order')
        for collection_group in collection_groups:
            group = get_object_or_404(
                ContextGroup, key=collection_group.context_group.key)
            group_services = ContextGroupServices.objects.filter(
                context_group=group).order_by('order')
            for group_service in group_services:
                csr_util = CSRUtils(
                    group_service.context_service_registry.key,
                    self.x,
                    self.y,
                    self.srid
                )
                cache = csr_util.retrieve_cache()

                # Append all the caches found locally - list still needed
                if cache is None:
                    util_arg = UtilArg(group_key=group.key,
                                       csr_util=csr_util)
                    util_arg_list.append(util_arg)
                else:
                    if group.key in group_caches:
                        group_caches[group.key].append(cache)
                    else:
                        group_caches[group.key] = [cache]

        # Parallel request external resources not found locally
        if len(util_arg_list) > 0:
            new_result_list = thread_retrieve_external(util_arg_list)

            # Add new external resources to dict with group: [cache]
            for new_util_arg in new_result_list:
                if new_util_arg is not None:
                    cache = new_util_arg.csr_util.create_cache()
                    if new_util_arg.group_key in group_caches:
                        group_caches[new_util_arg.group_key].append(cache)
                    else:
                        group_caches[new_util_arg.group_key] = [cache]

        # Init contextgroup parent and add group key
        for group_key, cache_list in group_caches.items():
            super(GroupValues, self).__init__(self.x, self.y, group_key, self.srid)
            for cache in cache_list:
                self.service_registry_values.append(cache)
            self.context_group_values.append("NOTSURE")
