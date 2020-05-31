import factory
from geocontext.models.csr import CSR
from geocontext.models.group_services import GroupServices
from geocontext.models.group import Group
from geocontext.models.collection_groups import CollectionGroups
from geocontext.models.collection import Collection


class CSRF(factory.DjangoModelFactory):
    class Meta:
        model = CSR

    key = factory.sequence(
        lambda n: f'TestCSRKey{n}')
    name = factory.sequence(
        lambda n: f'Test CSR name {n}')
    description = factory.sequence(
        lambda n: f'Test CSR description {n}')


class GroupServicesF(factory.DjangoModelFactory):
    class Meta:
        model = GroupServices


class GroupF(factory.DjangoModelFactory):
    class Meta:
        model = Group

    key = factory.sequence(
        lambda n: f'TestGroupKey{n}')
    name = factory.sequence(
        lambda n: f'Test Group name {n}')


class CollectionGroupsF(factory.DjangoModelFactory):
    class Meta:
        model = CollectionGroups


class CollectionF(factory.DjangoModelFactory):
    class Meta:
        model = Collection

    key = factory.sequence(
        lambda n: f'TestCollectionKey{n}')
    name = factory.sequence(
        lambda n: f'Test Collection name {n}')
