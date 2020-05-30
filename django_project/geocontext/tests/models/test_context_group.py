from django.test import TestCase

from geocontext.tests.models.model_factories import (
    ContextServiceRegistryF,
    ContextGroupF,
    ContextGroupServicesF,
)


class TestContextGroupRegistry(TestCase):
    """Test Context Group models"""

    def test_ContextGroup_create(self):
        """Test Context Group creation."""
        model = ContextGroupF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)

    def test_GroupServices_create(self):
        """Test Group Service Creation."""
        group = ContextGroupF.create()
        csr = ContextServiceRegistryF.create()

        self.assertEqual(group.context_service_registries.count(), 0)

        group_service = ContextGroupServicesF.create(
            context_group=group,
            context_service_registry=csr
        )

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.context_service_registries.count(), 1)

        self.assertEqual(group.context_service_registries.all()[0], csr)
