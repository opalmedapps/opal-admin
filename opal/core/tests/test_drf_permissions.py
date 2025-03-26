from typing import Any

from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils import timezone

import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework import exceptions, generics
from rest_framework.request import Request
from rest_framework.views import APIView

from opal.caregivers import factories as caregiver_factories
from opal.core import constants
from opal.patients import factories as patient_factories
from opal.patients.models import RelationshipStatus, RelationshipType
from opal.users.models import User

from .. import drf_permissions

pytestmark = pytest.mark.django_db(databases=['default'])


# See similar tests in opal/legacy/api/views/tests/test_caregiver_permissions.py > TestCaregiverPermissionsView
class TestCaregiverPatientPermissions:
    """Class wrapper for CaregiverPatientPermissions tests."""

    class_instance = drf_permissions.CaregiverPatientPermissions()

    def set_args(self, user_id: Any | None, patient_id: int | str | None) -> None:
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
        return self.class_instance.has_permission(Request(self.request), self.view)

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

    class_instance = drf_permissions.CaregiverSelfPermissions()

    def set_args(self, user_id: Any | None, patient_id: Any | None) -> None:
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
        return self.class_instance.has_permission(Request(self.request), self.view)

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


class _ModelView(generics.ListAPIView[User]):
    model = User
    queryset = User.objects.none()
    permission_classes = (drf_permissions.FullDjangoModelPermissions,)


class TestFullDjangoModelPermissions:
    """Class wrapper for FullDjangoModelPermissions tests."""

    methods = ['get', 'head', 'options', 'post', 'put', 'patch', 'delete']

    @pytest.mark.parametrize('method', methods)
    def test_unauthenticated(self, method: str) -> None:
        """Test that an unauthenticated request is rejected."""
        view = _ModelView()
        request = Request(RequestFactory().generic(method, '/'))

        assert not drf_permissions.FullDjangoModelPermissions().has_permission(request, view)

    @pytest.mark.parametrize('method', methods)
    def test_no_permission(self, method: str) -> None:
        """Test that a request with an authenticated user with no permission is rejected."""
        view = _ModelView()
        request = Request(RequestFactory().generic(method, '/'))
        request.user = User.objects.create(username='testuser')

        assert not drf_permissions.FullDjangoModelPermissions().has_permission(request, view)

    @pytest.mark.parametrize('method', methods)
    def test_with_permission(self, method: str) -> None:
        """Test that a request with user with the required permission (or a superuser) succeeds."""
        view = _ModelView()
        request = Request(RequestFactory().generic(method, '/'))
        request.user = User.objects.create(username='testuser', is_superuser=True)

        assert drf_permissions.FullDjangoModelPermissions().has_permission(request, view)


def test_issuperuser_unauthenticated() -> None:
    """The `IsSuperUser` permission requires an authenticated user."""
    request = Request(RequestFactory().get('/'))

    assert not drf_permissions.IsSuperUser().has_permission(request, APIView())


def test_issuperuser_unauthorized() -> None:
    """The `IsSuperUser` permission rejects users that are not a superuser."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser', is_staff=True)

    assert not drf_permissions.IsSuperUser().has_permission(request, APIView())


def test_issuperuser_authorized() -> None:
    """The `IsSuperUser` permission requires a superuser."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser', is_superuser=True)

    assert drf_permissions.IsSuperUser().has_permission(request, APIView())


def test_isormsuser_unauthenticated() -> None:
    """The `IsORMSUser` permission requires an authenticated user."""
    request = Request(RequestFactory().get('/'))

    assert not drf_permissions.IsORMSUser().has_permission(request, APIView())


def test_isormsuser_unauthorized() -> None:
    """The `IsSuperUser` permission rejects users that are not an ORMS user."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser', is_staff=True)

    assert not drf_permissions.IsORMSUser().has_permission(request, APIView())


def test_isormsuser_superuser() -> None:
    """The `IsORMSUser` permission allows access to a superuser."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser', is_superuser=True)

    assert drf_permissions.IsORMSUser().has_permission(request, APIView())


def test_isormsuser_orms_user(settings: SettingsWrapper) -> None:
    """The `IsORMSUser` permission grants access to an ORMS user."""
    request = Request(RequestFactory().get('/'))
    user = User.objects.create(username='testuser')
    user.groups.add(Group.objects.create(name=settings.ORMS_GROUP_NAME))
    request.user = user

    assert drf_permissions.IsORMSUser().has_permission(request, APIView())


def test_username_required_missing_attribute() -> None:
    """The UserNameRequired permission asserts that the required_username attribute is set."""
    with pytest.raises(ImproperlyConfigured):
        drf_permissions._UsernameRequired().has_permission(Request(HttpRequest()), APIView())


@pytest.mark.parametrize('permission_class', [
    drf_permissions.IsListener,
    drf_permissions.IsRegistrationListener,
    drf_permissions.IsInterfaceEngine,
    drf_permissions.IsLegacyBackend,
    drf_permissions.IsOrmsSystem,
])
def test_username_required_unauthenticated(permission_class: type[drf_permissions._UsernameRequired]) -> None:
    """The permissions require the user to be authenticated."""
    request = Request(RequestFactory().get('/'))

    assert not permission_class().has_permission(request, APIView())


@pytest.mark.parametrize('permission_class', [
    drf_permissions.IsListener,
    drf_permissions.IsRegistrationListener,
    drf_permissions.IsInterfaceEngine,
    drf_permissions.IsLegacyBackend,
    drf_permissions.IsOrmsSystem,
])
def test_username_required_admin_permitted(permission_class: type[drf_permissions._UsernameRequired]) -> None:
    """The permissions succeed if the user is an admin (superuser)."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser', is_superuser=True)

    assert permission_class().has_permission(request, APIView())


@pytest.mark.parametrize('permission_class', [
    drf_permissions.IsListener,
    drf_permissions.IsRegistrationListener,
    drf_permissions.IsInterfaceEngine,
    drf_permissions.IsLegacyBackend,
    drf_permissions.IsOrmsSystem,
])
def test_username_required_wrong_username(permission_class: type[drf_permissions._UsernameRequired]) -> None:
    """The permissions fail if the user does not have the expected username."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username='testuser')

    assert not permission_class().has_permission(request, APIView())


@pytest.mark.parametrize(('permission_class', 'username'), [
    (drf_permissions.IsListener, constants.USERNAME_LISTENER),
    (drf_permissions.IsRegistrationListener, constants.USERNAME_LISTENER_REGISTRATION),
    (drf_permissions.IsInterfaceEngine, constants.USERNAME_INTERFACE_ENGINE),
    (drf_permissions.IsLegacyBackend, constants.USERNAME_BACKEND_LEGACY),
    (drf_permissions.IsOrmsSystem, constants.USERNAME_ORMS),
])
def test_username_required_correct_username(
    permission_class: type[drf_permissions._UsernameRequired],
    username: str,
) -> None:
    """The permissions require the user to have the expected username."""
    request = Request(RequestFactory().get('/'))
    request.user = User.objects.create(username=username)

    assert permission_class().has_permission(request, APIView())
