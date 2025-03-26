"""Module providing API views for the `health_data` app."""
from typing import Any

from django.db import models
from django.utils import timezone

from rest_framework import generics, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import IsListener, IsORMSUser
from opal.patients.api.serializers import PatientUUIDSerializer
from opal.patients.models import Patient

from ..models import QuantitySample
from .serializers import QuantitySampleSerializer


class CreateQuantitySampleView(generics.CreateAPIView):
    """
    Create view for `QuantitySample`.

    Supports the creation of one or more instances at the same time by passing a list of dictionaries.
    """

    serializer_class = QuantitySampleSerializer
    # TODO: change to model permissions?
    # TODO: change in the future to limit to user with access to the patient
    # TODO: add CaregiverPermissions?
    permission_classes = (IsListener,)

    def get_serializer(self, *args: Any, **kwargs: Any) -> serializers.BaseSerializer[QuantitySample]:
        """
        Return the serializer for this API view.

        Sets the serializers `many` argument to `True` if a list is passed as the data.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the serializer instance
        """
        # support multiple elements
        # see: https://www.django-rest-framework.org/api-guide/serializers/#customizing-listserializer-behavior
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create one or more new quantity samples.

        Ensures that the patient with the uuid as part of the URL exists.
        Raises a 404 if the patient does not exist.

        Args:
            request: the API request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the response
        """
        uuid = self.kwargs['uuid']
        self.patient = generics.get_object_or_404(Patient.objects.all(), uuid=uuid)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer: serializers.BaseSerializer[QuantitySample]) -> None:
        """
        Perform the creation.

        Uses the patient instance determined according to the ID in the URL.

        Args:
            serializer: the serializer instance to use
        """
        serializer.save(patient=self.patient)


class UnviewedQuantitySampleView(APIView):
    """`GenericAPIView` for retrieving a list of patients' unviewed `QuantitySample` records."""

    permission_classes = (IsORMSUser,)

    def post(self, request: Request) -> Response:
        """Retrieve a list of patient's unviewed `QuantitySample` records.

        The method returns the counts (a.k.a. badges) of unviewed quantities for each patient.

        Args:
            request: HTTP request

        Returns:
            Response: list of unviewed `QuantitySample` counts for each patient
        """
        serializer = PatientUUIDSerializer(
            many=True,
            allow_empty=False,
            required=True,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        # Unviewed counts of patients' QuantitySamples
        unviewed_counts = Patient.objects.select_related(
            'quantity_samples',
        ).filter(
            uuid__in=[quantity['patient_uuid'] for quantity in serializer.validated_data],
            quantity_samples__viewed_at=None,
            quantity_samples__viewed_by='',
        ).annotate(
            count=models.Count('quantity_samples'),
            patient_uuid=models.F('uuid'),
        ).values('patient_uuid', 'count')

        return Response(data=unviewed_counts)


class MarkQuantitySampleAsViewedView(APIView):
    """`APIView` for setting patient's `QuantitySample` records as viewed."""

    permission_classes = (IsORMSUser,)

    def patch(self, request: Request, uuid: str) -> Response:
        """Set patient's `QuantitySample` records as viewed.

        Args:
            request: HTTP request
            uuid: patient's UUID for whom `QuantitySample` records are being set as viewed

        Returns:
            Response: successful response with no body
        """
        patient = generics.get_object_or_404(Patient.objects.all(), uuid=uuid)
        QuantitySample.objects.filter(
            patient=patient,
            viewed_at=None,
            viewed_by='',
        ).update(
            viewed_at=timezone.now(),
            viewed_by=request.user.get_username(),
        )

        # Return an empty response if patient's quantity samples updated successfully
        return Response()
