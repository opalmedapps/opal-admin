"""Module providing API views for the `health_data` app."""
from typing import Any

from django.db import models
from django.utils import timezone

from rest_framework import generics, permissions, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.core.drf_permissions import FullDjangoModelPermissions
from opal.patients.models import Patient

from ..models import QuantitySample
from .serializers import PatientUnviewedQuantitySampleSerializer, QuantitySampleSerializer


class CreateQuantitySampleView(generics.CreateAPIView):
    """
    Create view for `QuantitySample`.

    Supports the creation of one or more instances at the same time by passing a list of dictionaries.
    """

    serializer_class = QuantitySampleSerializer
    permission_classes = [permissions.IsAuthenticated]

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

    permission_classes = (FullDjangoModelPermissions,)
    serializer_class = PatientUnviewedQuantitySampleSerializer
    queryset = QuantitySample.objects.none()

    def post(self, request: Request) -> Response:
        """Retrieve a list of patient's unviewed `QuantitySample` records.

        The method returns the counts (a.k.a. badges) of unviewed quantities for each patient.

        Args:
            request: HTTP request

        Returns:
            Response: list of unviewed `QuantitySample` counts for each patient
        """
        serializer = self.serializer_class(
            many=True,
            allow_empty=False,
            required=True,
            data=self.request.data,
        )
        serializer.is_valid(raise_exception=True)

        # Return patients' unviewed counts of the QuantitySamples
        unviewed_samples = QuantitySample.objects.exclude(
            viewed_at=None,
            viewed_by='',
        ).filter(
            patient__uuid__in=[quantity['uuid']['uuid'] for quantity in serializer.validated_data],
        )

        # Use `order_by` to count distinct patient UUIDs
        # https://docs.djangoproject.com/en/4.2/topics/db/aggregation/#interaction-with-order-by
        unviewed_counts = unviewed_samples.values(
            'patient__uuid',
        ).annotate(
            patient_uuid=models.F('patient__uuid'),
            count=models.Count('patient'),
        ).order_by().values(
            'patient_uuid',
            'count',
        )
        return Response(data=unviewed_counts)


class ViewedQuantitySampleView(APIView):
    """`APIView` for setting patient's `QuantitySample` records as viewed."""

    # TODO: change to permission_classes = (IsOrms,) once permission is implemented
    permission_classes = (FullDjangoModelPermissions,)

    def patch(self, request: Request, uuid: str) -> Response:
        """Set patient's `QuantitySample` records as viewed.

        Args:
            request: HTTP request
            uuid: patient's UUID for whom `QuantitySample` records are being set as viewed

        Returns:
            Response: successful response with no body
        """
        patient = generics.get_object_or_404(Patient.objects.all(), uuid=uuid)
        QuantitySample.objects.filter(patient=patient).update(
            viewed_at=timezone.now(),
            viewed_by=request.user.get_username(),
        )

        # Return an empty response if patient's quantity samples updated successfully
        return Response()
