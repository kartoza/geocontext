from django.test import TestCase

from geocontext.tests.models.model_factories import (
    ContextServiceRegistryF,
    ContextGroupF,
    ContextGroupServicesF,
    ContextCollectionF,
    CollectionGroupsF,
)


class TestContextCollectionRegistry(TestCase):
    """Test Context Collection models"""

    def test_ContextCollection_create(self):
        """Test Context Collection creation."""
        model = ContextCollectionF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_CollectionGroups_create(self):
        """Test Collection Groups Creation."""
        group = ContextGroupF.create()
        csr = ContextServiceRegistryF.create()
        collection = ContextCollectionF.create()

        self.assertEqual(group.context_service_registries.count(), 0)
        self.assertEqual(collection.context_groups.count(), 0)

        group_service = ContextGroupServicesF.create(
            context_group=group,
            context_service_registry=csr
        )

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.context_service_registries.count(), 1)
        self.assertEqual(group.context_service_registries.all()[0], csr)

        group = CollectionGroupsF.create(
            context_collection=collection,
            context_group=group
        )

        self.assertEqual(collection.context_groups.count(), 1)
        self.assertEqual(collection.context_groups.all()[0], group)

        group.order = 0
        group.save()
