"""This module is an API view that returns the encryption value required to handle listener's registration requests."""
from typing import Any

from django.db.models.functions import SHA512
from django.db.models.query import QuerySet
from django.http import Http404

from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request, clone_request
from rest_framework.response import Response
from rest_framework.views import APIView

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


class UpdateDeviceView(UpdateAPIView):
    """Class handling requests for updates or creations of device ids."""

    permission_classes = [IsAuthenticated]
    serializer_class = UpdateDeviceSerializer
    lookup_url_kwarg = 'device_id'
    lookup_field = 'device_id'

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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
        elif self.request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        return Response({'status': status.HTTP_404_NOT_FOUND})

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a device id or create if it doesn't exist.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            HTTP `Response` success or failure
        """
        partial = self.kwargs.pop('partial', False)
        device_instance = self.get_object_or_none()
        serializer = self.get_serializer(
            device_instance,
            data=request.data,
            partial=partial,
        )

        if device_instance is None:
            lookup_value = self.kwargs[self.lookup_url_kwarg]
            extra_kwargs = {self.lookup_field: lookup_value}
            serializer.save(**extra_kwargs)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Set partial parameter and re-call update method.

        Args:
            request (Request): request object with parameters to update or create
            args (Any): varied amount of non-keyworded arguments
            kwargs (Any): varied amount of keyworded arguments

        Returns:
            self.update()
        """
        self.kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Device]:
        """Provide the desired object or fails with 404 error.

        Returns:
            Device object or 404.
        """
        return Device.objects.filter(device_id=self.kwargs['device_id'])

    def get_object_or_none(self) -> Any:
        """Attempt to retrieve object.

        If not found we use clone_request to check if the caller has the required permissions for a POST request.

        Returns:
            Device object, 404, or clone_request with POST action.

        Raises:
            Http404: the device is not found.

        """
        try:
            return self.get_object()
        except Http404:
            if self.request.method == 'PUT':
                # For PUT-as-create operation, we need to ensure that we have
                # relevant permissions, as if this was a POST request.  This
                # will either raise a PermissionDenied exception, or simply
                # return None.
                self.check_permissions(clone_request(self.request, 'POST'))
            else:
                # PATCH requests where the object does not exist should still
                # return a 404 response.
                raise


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
