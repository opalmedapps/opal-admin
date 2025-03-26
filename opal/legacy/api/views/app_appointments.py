"""Collection of api views used to get and update appointment details."""
from typing import Any

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import UpdateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener
from opal.legacy import models

from ..serializers import LegacyAppointmentCheckinSerializer, LegacyAppointmentDetailedSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='Appuserid',
            location=OpenApiParameter.HEADER,
            required=True,
            description='The username of the logged in user',
        ),
    ],
    responses=inline_serializer(
        name='AppAppointmentsSerializer',
        fields={
            'daily_appointments': LegacyAppointmentDetailedSerializer(many=True),
        },
    ),
)
class AppAppointmentsView(APIView):
    """Class to return appointments detail data."""

    permission_classes = (IsListener,)

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `api/app/home`.

        Args:
            request: Http request made by the listener.

        Returns:
            Http response with the data needed to display the home view.
        """
        username = request.headers['Appuserid']
        return Response({
            'daily_appointments': LegacyAppointmentDetailedSerializer(
                models.LegacyAppointment.objects.get_daily_appointments(username),
                many=True,
            ).data,
        })


class UpdateAppointmentCheckinView(UpdateAPIView[models.LegacyAppointment]):
    """View supporting single legacy appointment update based on patient legacy ID."""

    permission_classes = (IsListener,)
    serializer_class = LegacyAppointmentCheckinSerializer

    def get_object(self) -> models.LegacyAppointment:
        """
        Override get_object to filter by source_system_id and source_database.

        Raises:
            ValidationError: If one or both search parameters are omitted from request
            NotFound: If zero or multiple appointment records are found

        Returns:
            LegacyAppointment model instance
        """
        source_system_id = self.request.data.get('source_system_id')
        source_database = self.request.data.get('source_database')

        # Ensure both required fields are present
        if not source_system_id or not source_database:
            raise ValidationError("Both 'source_system_id' and 'source_database' are required.")
        try:
            return models.LegacyAppointment.objects.get(
                source_system_id=source_system_id,
                source_database=source_database,
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            # Ensure only one appointment is found
            raise NotFound(
                detail='Cannot find a unique appointment matching criteria.',
            )

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle a PATCH request to update an appointment instance.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response
        """
        return self.update(request, *args, **kwargs)
