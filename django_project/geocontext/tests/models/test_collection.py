from django.test import TestCase

from geocontext.tests.models.model_factories import (
    CSRF,
    GroupF,
    GroupServicesF,
    CollectionF,
    CollectionGroupsF,
)


class TestContextCollectionRegistry(TestCase):
    """Test Collection models"""

    def test_ContextCollection_create(self):
        """Test Context Collection creation."""
        model = CollectionF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_CollectionGroups_create(self):
        """Test Collection Groups Creation."""
        group = GroupF.create()
        csr = CSRF.create()
        collection = CollectionF.create()

        self.assertEqual(group.csr.count(), 0)
        self.assertEqual(collection.groups.count(), 0)

        group_service = GroupServicesF.create(group=group, csr=csr)

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.csr_list.count(), 1)
        self.assertEqual(group.csr_list.all()[0], csr)

        group = CollectionGroupsF.create(collection=collection, group=group)

        self.assertEqual(collection.groups.count(), 1)
        self.assertEqual(collection.groups.all()[0], group)

        group.order = 0
        group.save()
