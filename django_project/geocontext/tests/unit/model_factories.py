import factory

from django.contrib.auth.models import User
from django.utils import timezone

from geocontext.models import UserProfile, UserTier
from geocontext.models.service import Service
from geocontext.models.group import Group
from geocontext.models.group_services import GroupServices
from geocontext.models.collection import Collection
from geocontext.models.collection_groups import CollectionGroups


class UserF(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"username{n}")
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    email = factory.Sequence(lambda n: f"email{n}@example.com")
    password = ''
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = timezone.datetime(2000, 1, 1).replace(tzinfo=timezone.utc)
    date_joined = timezone.datetime(1999, 1, 1).replace(
        tzinfo=timezone.utc)

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class UserTierF(factory.django.DjangoModelFactory):
    class Meta:
        model = UserTier

    name = factory.Sequence(lambda n: f"name{n}")
    request_limit = '10/day'


class UserProfileF(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserF)
    user_tier = factory.SubFactory(UserTierF)


class ServiceF(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    key = factory.sequence(
        lambda n: f'TestServiceKey{n}')
    name = factory.sequence(
        lambda n: f'Test Service name {n}')
    description = factory.sequence(
        lambda n: f'Test Service description {n}')


class GroupServicesF(factory.django.DjangoModelFactory):
    class Meta:
        model = GroupServices


class GroupF(factory.django.DjangoModelFactory):
    class Meta:
        model = Group

    key = factory.sequence(
        lambda n: f'TestGroupKey{n}')
    name = factory.sequence(
        lambda n: f'Test Group name {n}')


class CollectionGroupsF(factory.django.DjangoModelFactory):
    class Meta:
        model = CollectionGroups


class CollectionF(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection

    key = factory.sequence(
        lambda n: f'TestCollectionKey{n}')
    name = factory.sequence(
        lambda n: f'Test Collection name {n}')
