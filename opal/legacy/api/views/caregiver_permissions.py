# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection of api views used for caregiver-patient permission checks."""

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.api.views import EmptyResponseSerializer
from opal.core.drf_permissions import CaregiverPatientPermissions, IsListener


class CaregiverPermissionsView(APIView):
    """
    Bare-bones API view used to perform a simple caregiver-patient permissions check.

    Validates that a caregiver has permission to view data for a specific patient (based on their relationship).
    Used by the legacy part of the listener to access functionality from CaregiverPatientPermissions.
    """

    # The essential work for this request is done by CaregiverPatientPermissions
    permission_classes = (IsListener, CaregiverPatientPermissions)
    serializer_class = EmptyResponseSerializer

    def get(self, request: Request, legacy_id: int) -> Response:
        """
        Handle GET requests on `patients/legacy/<legacy_id>/check-permissions`.

        Args:
            request: Http request made by the listener.
            legacy_id: The legacy ID used to represent the target patient.

        Returns:
            Http response containing no data if the permission checks succeed (200 OK), or a permission denied
            response if the permission checks fail.
        """
        # The following empty success response is only returned if CaregiverPatientPermissions succeeds
        return Response({})
