# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Unit tests for the allocation models"""

import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationStatusChoice,
)
from coldfront.core.project.models import Project
from coldfront.core.test_helpers.factories import (
    AllocationAttributeFactory,
    AllocationAttributeTypeFactory,
    AllocationFactory,
    AllocationStatusChoiceFactory,
    ProjectFactory,
    ResourceFactory,
)
import string
import random
import pickle

class AllocationModelTests(TestCase):
    """tests for Allocation model"""

    @classmethod
    def setUpTestData(cls):
        """Set up project to test model properties and methods"""
        cls.allocation = AllocationFactory()
        cls.allocation.resources.add(ResourceFactory(name="holylfs07/tier1"))

    def test_allocation_str(self):
        """test that allocation str method returns correct string"""
        allocation_str = "%s (%s)" % (self.allocation.get_parent_resource.name, self.allocation.project.pi)
        self.assertEqual(str(self.allocation), allocation_str)


class AllocationModelCleanMethodTests(TestCase):
    """tests for Allocation model clean method"""

    @classmethod
    def setUpTestData(cls):
        """Set up allocation to test clean method"""
        cls.active_status: AllocationStatusChoice = AllocationStatusChoiceFactory(name="Active")
        cls.expired_status: AllocationStatusChoice = AllocationStatusChoiceFactory(name="Expired")
        cls.project: Project = ProjectFactory()

    def test_status_is_expired_and_no_end_date_has_validation_error(self):
        """Test that an allocation with status 'expired' and no end date raises a validation error."""
        actual_allocation: Allocation = AllocationFactory.build(
            status=self.expired_status, end_date=None, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_expired_and_end_date_not_past_has_validation_error(self):
        """Test that an allocation with status 'expired' and end date in the future raises a validation error."""
        end_date_in_the_future: datetime.date = (timezone.now() + datetime.timedelta(days=1)).date()
        actual_allocation: Allocation = AllocationFactory.build(
            status=self.expired_status, end_date=end_date_in_the_future, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_expired_and_start_date_after_end_date_has_validation_error(self):
        """Test that an allocation with status 'expired' and start date after end date raises a validation error."""
        end_date: datetime.date = (timezone.now() + datetime.timedelta(days=1)).date()
        start_date_after_end_date: datetime.date = end_date + datetime.timedelta(days=1)

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.expired_status, start_date=start_date_after_end_date, end_date=end_date, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_expired_and_start_date_before_end_date_no_error(self):
        """Test that an allocation with status 'expired' and start date before end date does not raise a validation error."""
        start_date: datetime.date = datetime.datetime(year=2023, month=11, day=2, tzinfo=timezone.utc).date()
        end_date: datetime.date = start_date + datetime.timedelta(days=40)

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.expired_status, start_date=start_date, end_date=end_date, project=self.project
        )
        actual_allocation.full_clean()

    def test_status_is_expired_and_start_date_equals_end_date_no_error(self):
        """Test that an allocation with status 'expired' and start date equal to end date does not raise a validation error."""
        start_and_end_date: datetime.date = datetime.datetime(year=1997, month=4, day=20, tzinfo=timezone.utc).date()

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.expired_status, start_date=start_and_end_date, end_date=start_and_end_date, project=self.project
        )
        actual_allocation.full_clean()

    def test_status_is_active_and_no_start_date_has_validation_error(self):
        """Test that an allocation with status 'active' and no start date raises a validation error."""
        actual_allocation: Allocation = AllocationFactory.build(
            status=self.active_status, start_date=None, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_active_and_no_end_date_has_validation_error(self):
        """Test that an allocation with status 'active' and no end date raises a validation error."""
        actual_allocation: Allocation = AllocationFactory.build(
            status=self.active_status, end_date=None, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_active_and_start_date_after_end_date_has_validation_error(self):
        """Test that an allocation with status 'active' and start date after end date raises a validation error."""
        end_date: datetime.date = (timezone.now() + datetime.timedelta(days=1)).date()
        start_date_after_end_date: datetime.date = end_date + datetime.timedelta(days=1)

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.active_status, start_date=start_date_after_end_date, end_date=end_date, project=self.project
        )
        with self.assertRaises(ValidationError):
            actual_allocation.full_clean()

    def test_status_is_active_and_start_date_before_end_date_no_error(self):
        """Test that an allocation with status 'active' and start date before end date does not raise a validation error."""
        start_date: datetime.date = datetime.datetime(year=2001, month=5, day=3, tzinfo=timezone.utc).date()
        end_date: datetime.date = start_date + datetime.timedelta(days=160)

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.active_status, start_date=start_date, end_date=end_date, project=self.project
        )
        actual_allocation.full_clean()

    def test_status_is_active_and_start_date_equals_end_date_no_error(self):
        """Test that an allocation with status 'active' and start date equal to end date does not raise a validation error."""
        start_and_end_date: datetime.date = datetime.datetime(year=2005, month=6, day=3, tzinfo=timezone.utc).date()

        actual_allocation: Allocation = AllocationFactory.build(
            status=self.active_status, start_date=start_and_end_date, end_date=start_and_end_date, project=self.project
        )
        actual_allocation.full_clean()

class AllocationModelGetAttributeTests(TestCase):
    
    # | attr | expand | typed | situation code |
    # |    0 |      0 |     0 | nothing        |
    # |    0 |      0 |     1 | nothing        |
    # |    0 |      1 |     0 | nothing        |
    # |    0 |      1 |     1 | nothing        |
    # |    1 |      0 |     0 | value          |
    # |    1 |      0 |     1 | typed_value    |
    # |    1 |      1 |     0 | expanded_value |
    # |    1 |      1 |     1 | expanded_value |

    @staticmethod
    def __random_string(domain: str):
        # TODO: apply the FAKE_SEED to this random number generator once that infrastructure is put in
        return ''.join(random.choices(domain, k=random.randint(1, 8)))
    
    # TODO: replace magic_number with STRESS_LEVEL once that infrastructure is put in
    magic_number = 10

    def setUp(self):
        """
        Create an Allocation and associate AllocationAttributes with AllocationAttributeTypes 
        with type names following a sequence of integers.
        """
        self.allocation = AllocationFactory()
        for n in range(self.magic_number):
            undesired_type_name = str(n)
            undesired_allocation_attribute_type = AllocationAttributeTypeFactory(name=undesired_type_name)
            undesired_allocation_attribute = AllocationAttributeFactory(allocation=self.allocation, allocation_attribute_type=undesired_allocation_attribute_type)


    def _setup_and_run_for_no_attr_tests(self, expand: bool, typed: bool):
        """
        Pass the boolean arguments expand and typed into Allocation.get_attribute
        and assert that nothing changed and None was returned. The name is generated 
        randomly but will be guaranteed to never be the name of any other AllocationAttributeTypes
        placed in the database by the function. 
        """
        
        before_allocation_state = pickle.dumps(self.allocation.refresh_from_db())

        desired_type_name = self.__random_string(string.ascii_letters)
        actual = self.allocation.get_attribute(name=desired_type_name, expand=expand, typed=typed)

        after_allocation_state = pickle.dumps(self.allocation.refresh_from_db())

        self.assertIsNone(actual)
        self.assertEqual(before_allocation_state, after_allocation_state)

    def _setup_for_attr_tests(self) -> tuple[AllocationAttribute, str]:
        """
        Create a random name and an AllocationAttribute with an associated 
        AllocationAttributeFactory which are associated with the self.allocation 
        and return that AllocationAttribute and the name generated as a tuple.
        """
        desired_type_name = self.__random_string(string.ascii_letters)
        desired_allocation_attribute_type = AllocationAttributeTypeFactory(name=desired_type_name)
        desired_allocation_attribute = AllocationAttributeFactory(allocation=self.allocation, allocation_attribute_type=desired_allocation_attribute_type)
        desired_allocation_attribute.refresh_from_db()
        return desired_allocation_attribute, desired_type_name


    def test_no_attr_exists_and_not_expand_and_not_typed_does_nothing(self):
        expand = False
        typed = False
        self._setup_and_run_for_no_attr_tests(expand, typed)


    def test_no_attr_exists_and_not_expand_and_typed_does_nothing(self):
        expand = False
        typed = True
        self._setup_and_run_for_no_attr_tests(expand, typed)

    def test_no_attr_exists_and_expand_and_not_typed_does_nothing(self):
        expand = True
        typed = False
        self._setup_and_run_for_no_attr_tests(expand, typed)

    def test_no_attr_exists_and_expand_and_typed_does_nothing(self):
        expand = True
        typed = True
        self._setup_and_run_for_no_attr_tests(expand, typed)

    def test_attr_exists_and_not_expand_and_not_typed_returns_simple_value(self):
        desired_allocation_attribute, desired_name = self._setup_for_attr_tests()

        actual = self.allocation.get_attribute(desired_name, expand=False, typed=False)
        expected = desired_allocation_attribute.value

        self.assertIsInstance(actual, str)
        self.assertEqual(actual, expected)


    def test_attr_exists_and_not_expand_and_typed_returns_typed_value(self):
        desired_allocation_attribute, desired_name = self._setup_for_attr_tests()

        actual = self.allocation.get_attribute(desired_name, expand=False, typed=True)
        expected = desired_allocation_attribute.typed_value()

        self.assertIsInstance(actual, str)
        self.assertEqual(actual, expected)

    def test_attr_exists_and_expand_and_not_typed_returns_expanded_value(self):
        desired_allocation_attribute, desired_name = self._setup_for_attr_tests()

        actual = self.allocation.get_attribute(desired_name, expand=True, typed=False)
        expected = desired_allocation_attribute.expanded_value()

        self.assertIsInstance(actual, str)
        self.assertEqual(actual, expected)

    def test_attr_exists_and_expand_and_typed_returns_expanded_value(self):
        desired_allocation_attribute, desired_name = self._setup_for_attr_tests()

        actual = self.allocation.get_attribute(desired_name, expand=True, typed=True)
        expected = desired_allocation_attribute.expanded_value()

        self.assertIsInstance(actual, str)
        self.assertEqual(actual, expected)

    def test_no_attr_exists_default_kwargs_does_nothing(self):
        before_allocation_state = pickle.dumps(self.allocation.refresh_from_db())

        desired_type_name = self.__random_string(string.ascii_letters)
        actual = self.allocation.get_attribute(desired_type_name)

        after_allocation_state = pickle.dumps(self.allocation.refresh_from_db())

        self.assertIsNone(actual)
        self.assertEqual(before_allocation_state, after_allocation_state)

    def test_attr_exists_default_kwargs_returns_expanded_value(self):
        desired_allocation_attribute, desired_name = self._setup_for_attr_tests()

        actual = self.allocation.get_attribute(desired_name)
        expected = desired_allocation_attribute.expanded_value()

        self.assertIsInstance(actual, str)
        self.assertEqual(actual, expected)


