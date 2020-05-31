from django.test import TestCase

from geocontext.tests.models.model_factories import CSRF


class TestCSR(TestCase):
    """Test CSR models."""

    def test_CSR_create(self):
        """Test CSR model creation."""

        model = CSRF.create()

        # check if PK exists.
        self.assertTrue(model.pk is not None)

        # check if model key exists.
        self.assertTrue(model.key is not None)
