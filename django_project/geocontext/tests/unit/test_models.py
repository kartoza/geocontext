from django.test import TestCase

from geocontext.tests.models.model_factories import (
    ServiceF,
    GroupF,
    GroupServicesF,
    CollectionF,
    CollectionGroupsF,
)


class TestGroup(TestCase):
    """Test Group models"""

    def test_Group_create(self):
        """Test Group creation."""
        model = GroupF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_GroupServices_create(self):
        """Test Group Service Creation."""
        group = GroupF.create()
        service = ServiceF.create()

        self.assertEqual(group.services.count(), 0)

        group_service = GroupServicesF.create(group=group, services=service)

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.services.count(), 1)
        self.assertEqual(group.services.all()[0], service)


class TestService(TestCase):
    """Test Service models."""

    def test_Service_create(self):
        """Test Service model creation."""

        model = ServiceF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)


class TestCollection(TestCase):
    """Test Collection models"""

    def test_Collection_create(self):
        """Test Collection creation."""
        model = CollectionF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_CollectionGroups_create(self):
        """Test Collection Groups Creation."""
        group = GroupF.create()
        service = ServiceF.create()
        collection = CollectionF.create()

        self.assertEqual(group.services.count(), 0)
        self.assertEqual(collection.groups.count(), 0)

        group_service = GroupServicesF.create(group=group, services=service)

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.services.count(), 1)
        self.assertEqual(group.services.all()[0], service)

        collection_group = CollectionGroupsF.create(collection=collection, group=group)

        self.assertEqual(collection.groups.count(), 1)
        self.assertEqual(collection.groups.all()[0], group)

        collection_group.order = 0
        collection_group.save()
