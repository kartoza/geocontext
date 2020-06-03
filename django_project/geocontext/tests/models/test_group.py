from django.test import TestCase

from geocontext.tests.models.model_factories import (
    CSRF,
    GroupF,
    GroupServicesF,
)


class TestGroupRegistry(TestCase):
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
        csr = CSRF.create()

        self.assertEqual(group.csr_list.count(), 0)

        group_service = GroupServicesF.create(group=group, csr=csr)

        group_service.order = 0
        group_service.save()

        self.assertEqual(group.csr_list.count(), 1)
        self.assertEqual(group.csr_list.all()[0], csr)
