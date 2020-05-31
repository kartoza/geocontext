import os

from django.conf import settings
from django.test import TestCase

from base.management.commands.utilities import import_data, delete_data


class TestGeoContextView(TestCase):
    """Test for geocontext view."""

    def tearDown(self):
        """Run after finished."""
        delete_data()

    def test_import_geocontext_data(self):
        """Setup test data."""
        geocontext_path = os.path.join(
            settings.BASE_DIR, '../base/management/commands/geocontext.json', )
        self.assertTrue(os.path.exists(geocontext_path))
        # It should not raise an error
        import_data(geocontext_path)
