"""This module provides `APIViews` for the `patients` app REST APIs."""

from typing import Any, Type

from django.db.models.query import QuerySet

from rest_framework import serializers
from rest_framework.generics import ListAPIView, RetrieveAPIView

from opal.caregivers.api.serializers import RegistrationCodePatientDetailedSerializer, RegistrationCodePatientSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.patients.api.serializers import MyCaregiversSerializer
from opal.patients.models import Relationship


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        RegistrationCode.objects.select_related(
            'relationship',
            'relationship__patient',
        ).prefetch_related(
            'relationship__patient__hospital_patients',
        ).filter(status=RegistrationCodeStatus.NEW)
    )

    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_serializer_class(self, *args: Any, **kwargs: Any) -> Type[serializers.BaseSerializer]:
        """Override 'get_serializer_class' to switch the serializer based on the GET parameter `detailed`.

        Args:
            args (list): request parameters
            kwargs (dict): request parameters

        Returns:
            The expected serializer according to the request parameter.
        """
        if 'detailed' in self.request.query_params:
            return RegistrationCodePatientDetailedSerializer

        return RegistrationCodePatientSerializer


class GetCaregiverList(ListAPIView):
    """Class returning list of caregivers for a given patient."""

    serializer_class = MyCaregiversSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Relationship]:
        """Query set to retrieve list of caregivers for the input patient.

        Returns:
            List of caregivers profile for a given patient
        """
        return Relationship.objects.filter(patient__legacy_id=self.kwargs['legacy_patient_id'])
