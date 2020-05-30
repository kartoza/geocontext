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
        lambda n: f'TestCSRKey{n}')
    name = factory.sequence(
        lambda n: f'Test CSR name {n}')
    description = factory.sequence(
        lambda n: f'Test CSR description {n}')


class ContextGroupServicesF(factory.DjangoModelFactory):
    class Meta:
        model = ContextGroupServices


class ContextGroupF(factory.DjangoModelFactory):
    class Meta:
        model = ContextGroup

    key = factory.sequence(
        lambda n: f'TestContextGroupKey{n}')
    name = factory.sequence(
        lambda n: f'Test Context Group name {n}')


class CollectionGroupsF(factory.DjangoModelFactory):
    class Meta:
        model = CollectionGroups


class ContextCollectionF(factory.DjangoModelFactory):
    class Meta:
        model = ContextCollection

    key = factory.sequence(
        lambda n: f'TestContextCollectionKey{n}')
    name = factory.sequence(
        lambda n: f'Test Context Collection name {n}')
