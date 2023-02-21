"""This module provides custom permissions for the Django REST framework.

These permissions are provided for the project and intended to be reused.
"""
from typing import TYPE_CHECKING, Optional

from django.db.models import QuerySet
from django.http import HttpRequest

from rest_framework import exceptions, permissions

from opal.caregivers.models import CaregiverProfile
from opal.patients.models import Relationship, RelationshipStatus, RoleType

if TYPE_CHECKING:
    from rest_framework.views import APIView


class CustomDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Custom DRF `DjangoModelPermissions` permission which is more restrictive.

    Restricts GET operations to require the `view` permission on the model.

    See: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions
    """

    # taken from DjangoModelPermissions and added the permission for GET
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class CaregiverPatientPermissions(permissions.BasePermission):
    """
    Global permission check that validates the permission of a caregiver trying to access a patient's data.

    Requirements:
        request.headers['Appuserid']: The caregiver's username.
        legacy_id (from the view's kwargs): The patient's legacy ID.
    """

    def has_permission(self, request: HttpRequest, view: 'APIView') -> bool:  # noqa: WPS210
        """
        Permission check that looks for a confirmed relationship between a caregiver and a patient.

        If found, the permission is granted, otherwise, it's rejected with a detailed message.
        Requirements (input parameters) expected by this function are described in the class-level docstring above.

        Args:
            request: The http request to allow or deny.
            view: The view through which the request was made.

        Returns:
            True if the caregiver has a confirmed relationship with the patient.
        """
        # Read and validate the input parameters
        caregiver_username = self._get_caregiver_username(request)
        patient_legacy_id = self._get_patient_legacy_id(view)

        # Perform the permission checks
        caregiver_profile = self._check_caregiver_exists(caregiver_username)
        relationships_with_target = self._check_has_relationship_with_target(caregiver_profile, patient_legacy_id)
        self._check_has_valid_relationship(relationships_with_target)

        return True

    def _get_caregiver_username(self, request: HttpRequest) -> str:
        """
        Validate the existence of a caregiver username provided as input, and return it if provided.

        Args:
            request: The http request.

        Raises:
            ParseError: If the caregiver username was not provided.

        Returns:
            The caregiver username.
        """
        caregiver_username = request.headers.get('Appuserid')
        if not caregiver_username or not isinstance(caregiver_username, str):
            raise exceptions.ParseError(
                'Requests to APIs using CaregiverPatientPermissions must provide a string'
                + " 'Appuserid' header representing the current user.",
            )
        return caregiver_username

    def _get_patient_legacy_id(self, view: 'APIView') -> int:
        """
        Validate the existence of a patient's legacy id provided as input, and return it if provided.

        Args:
            view: The view through which the request was made.

        Raises:
            ParseError: If the patient's legacy id was not provided.

        Returns:
            The patient's legacy id.
        """
        patient_legacy_id = view.kwargs.get('legacy_id') if hasattr(view, 'kwargs') else None
        if not patient_legacy_id or not isinstance(patient_legacy_id, int):
            raise exceptions.ParseError(
                'Requests to APIs using CaregiverPatientPermissions must provide an integer'
                + " 'legacy_id' URL argument representing the target patient.",
            )
        return patient_legacy_id

    def _check_caregiver_exists(self, caregiver_username: Optional[str]) -> CaregiverProfile:
        """
        Validate the existence of a CaregiverProfile matching the input caregiver username, and return it if found.

        Args:
            caregiver_username: The caregiver username used to search for a matching CaregiverProfile.

        Raises:
            PermissionDenied: If the caregiver is not found.

        Returns:
            The CaregiverProfile.
        """
        caregiver_profile = CaregiverProfile.objects.filter(user__username=caregiver_username).first()
        if not caregiver_profile:
            raise exceptions.PermissionDenied('Caregiver not found.')
        return caregiver_profile

    def _check_has_relationship_with_target(
        self,
        caregiver_profile: CaregiverProfile,
        patient_legacy_id: int,
    ) -> QuerySet[Relationship]:
        """
        Validate the existence of one or more Relationships between a caregiver and a patient, and return them if found.

        Args:
            caregiver_profile: The caregiver profile used to search for Relationships.
            patient_legacy_id: The patient legacy id representing the patient who should be part of the Relationship(s).

        Raises:
            PermissionDenied: If the caregiver has no relationships with the patient.

        Returns:
            The set of relationships between the caregiver and patient.
        """
        relationships_with_target = caregiver_profile.relationships.filter(
            patient__legacy_id=patient_legacy_id,
        )
        if not relationships_with_target:
            raise exceptions.PermissionDenied('Caregiver does not have a relationship with the patient.')
        return relationships_with_target

    def _check_has_valid_relationship(self, relationships_with_target: QuerySet[Relationship]) -> None:
        """
        Validate whether at least one of the relationships between a patient and caregiver has a CONFIRMED status.

        Return all such relationships from the list if found.

        Args:
            relationships_with_target: The list of relationships between the caregiver and patient to check.

        Raises:
            PermissionDenied: If none of the provided relationships have a confirmed status.
        """
        valid_relationships = [rel for rel in relationships_with_target if rel.status == RelationshipStatus.CONFIRMED]
        if not valid_relationships:
            raise exceptions.PermissionDenied(
                "Caregiver has a relationship with the patient, but its status is not CONFIRMED ('CON').",
            )


class UpdateModelPermissions(permissions.DjangoModelPermissions):
    """
    Custom DRF `DjangoModelPermissions` permission for changing/updating a model's data.

    Restricts PUT and PATCH operations to require the `view` permission on the model.

    See: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions
    """

    # taken from DjangoModelPermissions and added the permission for PUT and PATCH
    perms_map = {
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
    }


class CaregiverSelfPermissions(CaregiverPatientPermissions):
    """
    Global permission check that validates the permission of a caregiver trying to access a patient's data.

    Additionally, this check returns True only if the caregiver has a self relationshiptype role with the patient.

    Requirements:
        request.headers['Appuserid']: The caregiver's username.
        legacy_id (from the view's kwargs): The patient's legacy ID.
    """

    def has_permission(self, request: HttpRequest, view: 'APIView') -> bool:  # noqa: WPS210
        """
        Permission check that looks for a confirmed self relationship between a caregiver and a patient.

        If found, the permission is granted, otherwise, it's rejected with a detailed message.
        Requirements (input parameters) expected by this function are described in the class-level docstring above.

        Args:
            request: The http request to allow or deny.
            view: The view through which the request was made.

        Returns:
            True if the caregiver has a confirmed relationship with the patient.
        """
        # Read and validate the input parameters
        caregiver_username = self._get_caregiver_username(request)
        patient_legacy_id = self._get_patient_legacy_id(view)

        # Perform the permission checks
        caregiver_profile = self._check_caregiver_exists(caregiver_username)
        relationships_with_target = self._check_has_relationship_with_target(caregiver_profile, patient_legacy_id)
        self._check_has_valid_relationship(relationships_with_target)  # Has confirmed relationships
        self._check_has_self_relationship_type(relationships_with_target)  # Has confirmed, SELF relationship(s)

        return True

    def _check_has_self_relationship_type(self, relationships_with_target: QuerySet[Relationship]) -> None:
        """
        Validate whether at least one of the relationships between a patient and caregiver has a SELF role type.

        Args:
            relationships_with_target: The list of relationships between the caregiver and patient to check.

        Raises:
            PermissionDenied: If none of the provided relationships have a SELF status.
        """
        valid_relationships = [rel for rel in relationships_with_target if rel.type.role_type == RoleType.SELF]
        if not valid_relationships:
            raise exceptions.PermissionDenied(
                'Caregiver has a confirmed relationship with the patient, but its role type is not SELF.',
            )

# Future Enhancement: Pull common permissions functionality into an abstract base class
#                     to allow for faster definition of new perms in the future
