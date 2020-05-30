from django.test import TestCase

from geocontext.tests.models.model_factories import ContextServiceRegistryF


class TestContextServiceRegistry(TestCase):
    """Test CSR models."""

    def test_ContextServiceRegistry_create(self):
        """Test CSR model creation."""

        model = ContextServiceRegistryF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)
