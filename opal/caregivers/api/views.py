"""This module is an API view that returns the encryption value required to handle listener's registration requests."""
from typing import Any

from django.db.models.functions import SHA512
from django.db.models.query import QuerySet

from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.mixins.put_as_create import AllowPUTAsCreateMixin
from opal.caregivers.api.serializers import RegistrationEncryptionInfoSerializer, UpdateDeviceSerializer
from opal.caregivers.models import Device, RegistrationCode, RegistrationCodeStatus
from opal.patients.api.serializers import CaregiverPatientSerializer
from opal.patients.models import Relationship


class GetRegistrationEncryptionInfoView(RetrieveAPIView):
    """Class handling gets requests for registration encryption values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).annotate(code_sha512=SHA512('code')).filter(status=RegistrationCodeStatus.NEW)
    )
    serializer_class = RegistrationEncryptionInfoSerializer
    lookup_url_kwarg = 'hash'
    lookup_field = 'code_sha512'


class UpdateDeviceView(AllowPUTAsCreateMixin):
    """Class handling requests for updates or creations of device ids."""

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateDeviceSerializer
    lookup_url_kwarg = 'device_id'
    lookup_field = 'device_id'

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Any:
        """Handle incoming put request and redirect to update method.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` success or failure
        """
        if self.request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        return Response({'status': status.HTTP_404_NOT_FOUND})

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Any:
        """Handle incoming path request and redirect to partial update method.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` success or failure
        """
        if self.request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        return Response({'status': status.HTTP_404_NOT_FOUND})

    def get_queryset(self) -> QuerySet[Device]:
        """Provide the desired object or fails with 404 error.

        Returns:
            Device object or 404.
        """
        return Device.objects.filter(device_id=self.kwargs['device_id'])


class GetCaregiverPatientsList(APIView):
    """Class to return a list of patients for a given caregiver."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Handle GET requests from `caregivers/patients/`.

        Args:
            request: Http request made by the listener needed to retrive `Appuserid`.

        Returns:
            Http response with the list of patients for a given caregiver.
        """
        user_id = request.headers.get('Appuserid')
        if user_id:
            relationships = Relationship.objects.get_patient_list_for_caregiver(user_id)
            response = Response(
                CaregiverPatientSerializer(relationships, many=True).data,
            )
        else:
            response = Response([], status=status.HTTP_400_BAD_REQUEST)

        return response
