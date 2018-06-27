# coding=utf-8
"""Factories for building model instances for testing."""

import factory
from geocontext.models.context_service_registry import ContextServiceRegistry
from geocontext.models.context_group_services import ContextGroupServices
from geocontext.models.context_group import ContextGroup
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.context_collection import ContextCollection


class ContextServiceRegistryF(factory.DjangoModelFactory):
    class Meta:
        model = ContextServiceRegistry

    key = factory.sequence(
        lambda n: u'TestCSRKey%s' % n)
    name = factory.sequence(
        lambda n: u'Test CSR name %s' % n)
    description = factory.sequence(
        lambda n: u'Test CSR description %s' % n)


class ContextGroupServicesF(factory.DjangoModelFactory):
    class Meta:
        model = ContextGroupServices


class ContextGroupF(factory.DjangoModelFactory):
    class Meta:
        model = ContextGroup

    key = factory.sequence(
        lambda n: u'TestContextGroupKey%s' % n)
    name = factory.sequence(
        lambda n: u'Test Context Group name %s' % n)


class CollectionGroupsF(factory.DjangoModelFactory):
    class Meta:
        model = CollectionGroups


class ContextCollectionF(factory.DjangoModelFactory):
    class Meta:
        model = ContextCollection

    key = factory.sequence(
        lambda n: u'TestContextCollectionKey%s' % n)
    name = factory.sequence(
        lambda n: u'Test Context Collection name %s' % n)
