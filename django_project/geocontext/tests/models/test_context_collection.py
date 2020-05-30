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
        context_group = ContextGroupF.create()
        context_service_registry = ContextServiceRegistryF.create()
        context_collection = ContextCollectionF.create()

        self.assertEqual(context_group.context_service_registries.count(), 0)
        self.assertEqual(context_collection.context_groups.count(), 0)

        context_group_service = ContextGroupServicesF.create(
            context_group=context_group,
            context_service_registry=context_service_registry
        )

        context_group_service.order = 0
        context_group_service.save()

        self.assertEqual(context_group.context_service_registries.count(), 1)
        self.assertEqual(
            context_group.context_service_registries.all()[0],
            context_service_registry
        )

        collection_group = CollectionGroupsF.create(
            context_collection=context_collection,
            context_group=context_group
        )

        self.assertEqual(context_collection.context_groups.count(), 1)
        self.assertEqual(
            context_collection.context_groups.all()[0],
            context_group
        )

        collection_group.order = 0
        collection_group.save()
