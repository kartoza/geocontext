from datetime import datetime
import os

from django.test import TestCase

from geocontext.models.csr import CSR
from geocontext.models.utilities import CSRUtils
from base.management.commands.utilities import import_data

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestGeoContextView(TestCase):
    """Test for geocontext view."""

    def setUp(self):
        """Setup test data."""
        test_geocontext_file = os.path.join(
            test_data_directory, 'test_geocontext.json')
        import_data(test_geocontext_file)
        pass

    def tearDown(self):
        """Delete all service registry data."""
        csr_lisr = CSR.objects.all()
        for csr in csr_lisr:
            csr.delete()

    def test_cache_retrieval(self):
        """Test for retrieving from service registry and cache."""
        x = 27.8
        y = -32.1
        csr_key = 'quaternary_catchment_area'

        start_direct = datetime.now()
        csr_util = CSRUtils(csr_key, x, y)
        csr_util.retrieve_cache()

        end_direct = datetime.now()

        start_cache = datetime.now()
        csr_util.retrieve_cache()
        end_cache = datetime.now()

        duration_direct = end_direct - start_direct
        duration_cache = end_cache - start_cache
        direct_time = duration_direct.total_seconds()
        cache_time = duration_cache.total_seconds()
        message = f'Direct: {direct_time:.5f}. Cache: {cache_time:.5f}'
        self.assertGreater(duration_direct, duration_cache, message)
