"""
This module provides custom permissions for the Django REST framework.

These permissions are provided for the project and intended to be reused.
"""
from django.http import HttpRequest

from rest_framework import permissions

from ..caregivers.models import CaregiverProfile
from ..patients.models import Relationship, RelationshipStatus


class CustomDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Custom DRF `DjangoModelPermissions` permission which is more restrictive.

    Restricts GET operations to require the `view` permission on the model.

    See: https://www.django-rest-framework.org/api-guide/permissions/#djangomodelpermissions
    """

    # taken from DjangoModelPermissions and added the permission for GET
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],  # noqa: WPS323
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],  # noqa: WPS323
        'PUT': ['%(app_label)s.change_%(model_name)s'],  # noqa: WPS323
        'PATCH': ['%(app_label)s.change_%(model_name)s'],  # noqa: WPS323
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],  # noqa: WPS323
    }


class CaregiverPatientPermissions(permissions.BasePermission):
    """
    Global permission check that validates the permission of a caregiver trying to access a patient's data.

    Requirements:
        request.headers['Appuserid']: The caregiver's username.
        legacy_id (from the view's kwargs): The patient's legacy ID.
    """

    # view: APIView (cannot import due to circular dependency)
    def has_permission(self, request: HttpRequest, view) -> bool:  # type: ignore  # noqa: WPS231
        """
        Permission check that looks for a confirmed relationship between a caregiver and a patient.

        If found, the permission is granted, otherwise, it's rejected with a detailed message.

        Args:
            request: The http request to allow or deny.
            view: The view through which the request was made.

        Returns:
            True if the caregiver has a confirmed relationship with the patient; false otherwise.
        """
        caregiver_username = request.headers.get('Appuserid')
        patient_legacy_id = view.kwargs.get('legacy_id')

        # Find the caregiver
        self_caregiver_profile = CaregiverProfile.objects.filter(
            user__username=caregiver_username,
        ).prefetch_related('relationships__patient').first()

        # Get the list of relationships between the caregiver and the target patient
        relationships_with_target = self_caregiver_profile.relationships.filter(
            patient__legacy_id=patient_legacy_id,
        ) if self_caregiver_profile else Relationship.objects.none()

        # Check whether the caregiver has at least one confirmed relationship with the target patient
        has_valid_relationship = bool(
            [rel for rel in relationships_with_target if rel.status == RelationshipStatus.CONFIRMED],
        )

        # Set BasePermission's message field to explain the returned result (non-user-facing)
        if not caregiver_username:  # noqa: WPS223
            self.message = "Requests to APIs using CaregiverPatientPermissions must provide an 'Appuserid' header representing the current user."  # noqa: E501
        elif not patient_legacy_id:
            self.message = "Requests to APIs using CaregiverPatientPermissions must provide a 'legacy_id' URL argument representing the target patient."  # noqa: E501
        elif not self_caregiver_profile:
            self.message = 'Caregiver not found.'
        elif not relationships_with_target:
            self.message = 'Caregiver does not have a relationship with the patient.'
        elif not has_valid_relationship:
            self.message = "Caregiver has a relationship with the patient, but its status is not CONFIRMED ('CON')."

        return has_valid_relationship
