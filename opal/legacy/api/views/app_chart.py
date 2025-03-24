# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection of api views used to display the Opal's Chart view."""
from typing import Any

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.legacy import models
from opal.legacy_questionnaires.models import LegacyQuestionnaire

from ..serializers import UnreadCountSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='Appuserid',
            location=OpenApiParameter.HEADER,
            required=True,
            description='The username of the logged in user',
        ),
    ],
    responses={
        200: UnreadCountSerializer,
    },
)
class AppChartView(APIView):
    """Class to return chart page required data."""

    permission_classes = (IsListener,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle GET requests from `api/app/chart`.

        The function provides the number of unread values for the user
        and will provide them for the selected patient instead until the profile selector is finished.

        Args:
            request: http request used to get username making the request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            Http response with the data needed to display the chart view.
        """
        legacy_id = kwargs['legacy_id']
        username = request.headers['Appuserid']
        unread_count = {
            'unread_appointment_count': models.LegacyAppointment.objects.get_unread_queryset(
                legacy_id,
                username,
            ).count(),
            'unread_lab_result_count': models.LegacyPatientTestResult.objects.get_unread_queryset(
                legacy_id,
                username,
            ).count(),
            'unread_document_count': models.LegacyDocument.objects.get_unread_queryset(
                legacy_id,
                username,
            ).count(),
            'unread_txteammessage_count': models.LegacyTxTeamMessage.objects.get_unread_queryset(
                legacy_id,
                username,
            ).count(),
            'unread_educationalmaterial_count': models.LegacyEducationalMaterial.objects.get_unread_queryset(
                legacy_id,
                username,
            ).filter(
                educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Clinical',
            ).count(),
            'unread_questionnaire_count': LegacyQuestionnaire.objects.new_questionnaires(
                legacy_id,
                username,
                1,
            ).count(),
            'unread_research_reference_count': models.LegacyEducationalMaterial.objects.get_unread_queryset(
                legacy_id,
                username,
            ).filter(
                educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Research',
            ).count(),
            'unread_research_questionnaire_count': LegacyQuestionnaire.objects.new_questionnaires(
                legacy_id,
                username,
                2,
            ).count(),
            'unread_consent_questionnaire_count': LegacyQuestionnaire.objects.new_questionnaires(
                legacy_id,
                username,
                4,
            ).count(),
        }

        return Response(UnreadCountSerializer(unread_count).data)
