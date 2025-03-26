from typing import Any, Optional

from django.http import HttpRequest
from django.utils import timezone

import pytest
from rest_framework import exceptions
from rest_framework.views import APIView

from opal.caregivers import factories as caregiver_factories
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipStatus, RelationshipType

from ..drf_permissions import CaregiverPatientPermissions, CaregiverSelfPermissions

pytestmark = pytest.mark.django_db(databases=['default'])


# See similar tests in opal/legacy/tests/test_views.py > TestCaregiverPermissionsView
class TestCaregiverPatientPermissions:
    """Class wrapper for CaregiverPatientPermissions tests."""

    class_instance = CaregiverPatientPermissions()

    def set_args(self, user_id: Optional[Any], patient_id: Optional[Any]) -> None:
        """Set the input arguments expected by CaregiverPatientPermissions."""
        if user_id:
            self.request.META['HTTP_Appuserid'] = user_id
        if patient_id:
            self.view.kwargs = {'legacy_id': patient_id}

    def has_permission(self) -> bool:
        """
        Execute the call to the permissions check.

        Returns:
            The result of calling CaregiverPatientPermissions; i.e., whether the permission is granted.
        """
        return self.class_instance.has_permission(self.request, self.view)

    def test_no_caregiver_username(self) -> None:
        """Test with no provided 'Appuserid'."""
        caregiver_factories.CaregiverProfile()
        self.set_args(user_id=None, patient_id=99)

        with pytest.raises(exceptions.ParseError) as exception_info:
            self.has_permission()

        assert "must provide a string 'Appuserid'" in str(exception_info.value)

    def test_non_string_caregiver_username(self) -> None:
        """Test with an 'Appuserid' that's not a string."""
        self.set_args(1, patient_id=None)

        with pytest.raises(exceptions.ParseError) as exception_info:
            self.has_permission()

        assert "must provide a string 'Appuserid'" in str(exception_info.value)

    def test_no_patient_id(self) -> None:
        """Test with no provided 'legacy_id'."""
        caregiver = caregiver_factories.CaregiverProfile()
        self.set_args(caregiver.user.username, patient_id=None)

        with pytest.raises(exceptions.ParseError) as exception_info:
            self.has_permission()

        assert "must provide an integer 'legacy_id'" in str(exception_info.value)

    def test_non_integer_patient_id(self) -> None:
        """Test with a 'legacy_id' that's not an integer."""
        caregiver = caregiver_factories.CaregiverProfile()
        self.set_args(caregiver.user.username, patient_id='a')

        with pytest.raises(exceptions.ParseError) as exception_info:
            self.has_permission()

        assert "must provide an integer 'legacy_id'" in str(exception_info.value)

    def test_caregiver_not_found(self) -> None:
        """Test providing a username that doesn't exist."""
        caregiver_factories.CaregiverProfile()
        self.set_args('wrong_username', patient_id=99)

        with pytest.raises(exceptions.PermissionDenied) as exception_info:
            self.has_permission()

        assert 'Caregiver not found' in str(exception_info.value)

    def test_no_relationship(self) -> None:
        """Test a permissions check where the caregiver doesn't have a relationship with the patient."""
        caregiver = caregiver_factories.CaregiverProfile()
        patient = patient_factories.Patient()
        self.set_args(caregiver.user.username, patient.legacy_id)

        with pytest.raises(exceptions.PermissionDenied) as exception_info:
            self.has_permission()

        assert 'does not have a relationship' in str(exception_info.value)

    def test_unconfirmed_relationship(self) -> None:
        """Test a permissions check where the caregiver has a relationship with the patient, but it isn't confirmed."""
        relationship = patient_factories.Relationship()
        self.set_args(relationship.caregiver.user.username, relationship.patient.legacy_id)

        with pytest.raises(exceptions.PermissionDenied) as exception_info:
            self.has_permission()

        assert 'status is not CONFIRMED' in str(exception_info.value)

    def test_deceased_patient(self) -> None:
        """Test that the permission check fails if the patient is deceased."""
        relationship = patient_factories.Relationship(
            status=RelationshipStatus.CONFIRMED,
            patient__date_of_death=timezone.now(),
        )
        self.set_args(relationship.caregiver.user.username, relationship.patient.legacy_id)

        with pytest.raises(exceptions.PermissionDenied) as exception_info:
            self.has_permission()

        assert 'Patient has a date of death recorded' in str(exception_info.value)

    def test_success_confirmed_relationship(self) -> None:
        """Test a permissions check where the caregiver has a confirmed relationship with the patient."""
        relationship = patient_factories.Relationship(status=RelationshipStatus.CONFIRMED)
        self.set_args(relationship.caregiver.user.username, relationship.patient.legacy_id)

        assert self.has_permission()

    @pytest.fixture(autouse=True)
    def _before_each(self) -> None:
        """Create request and view objects for each test."""
        self.request = HttpRequest()
        self.view = APIView()


class TestCaregiverSelfPermissions:
    """Class wrapper for CaregiverSelfPermissions tests."""

    class_instance = CaregiverSelfPermissions()

    def set_args(self, user_id: Optional[Any], patient_id: Optional[Any]) -> None:
        """Set the input arguments expected by CaregiverPatientPermissions."""
        if user_id:
            self.request.META['HTTP_Appuserid'] = user_id
        if patient_id:
            self.view.kwargs = {'legacy_id': patient_id}

    def has_permission(self) -> bool:
        """
        Execute the call to the permissions check.

        Returns:
            The result of calling CaregiverPatientPermissions; i.e., whether the permission is granted.
        """
        return self.class_instance.has_permission(self.request, self.view)

    def test_non_self_relationship_type(self) -> None:
        """Test a permissions check where the caregiver has a relationship with the patient, but it isn't self typed."""
        relationship = patient_factories.Relationship(status=RelationshipStatus.CONFIRMED)
        self.set_args(relationship.caregiver.user.username, relationship.patient.legacy_id)

        with pytest.raises(exceptions.PermissionDenied) as exception_info:
            self.has_permission()

        assert 'role type is not SELF' in str(exception_info.value)

    def test_success_self_relationship_type(self) -> None:
        """Test a permissions check where the caregiver has a self relationship with the patient."""
        relationship = patient_factories.Relationship(
            status=RelationshipStatus.CONFIRMED,
            type=RelationshipType.objects.self_type(),
        )
        self.set_args(relationship.caregiver.user.username, relationship.patient.legacy_id)

        assert self.has_permission()

    @pytest.fixture(autouse=True)
    def _before_each(self) -> None:
        """Create request and view objects for each test."""
        self.request = HttpRequest()
        self.view = APIView()
