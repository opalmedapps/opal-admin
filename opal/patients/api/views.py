"""This module is an API view that returns the patient detaild and non-detailed info via registration code."""

from typing import Any

from rest_framework.generics import RetrieveAPIView

from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.patients.api.serializer import RegistrationCodePatientDetailedSerializer, RegistrationCodePatientSerializer


class RetrieveRegistrationDetailsView(RetrieveAPIView):
    """Class handling GET requests for registration code values."""

    queryset = (
        RegistrationCode.objects.filter(status=RegistrationCodeStatus.NEW)
    )

    lookup_url_kwarg = 'code'
    lookup_field = 'code'

    def get_serializer_class(self, *args: Any, **kwargs: Any) -> Any:
        """Override get_serializer_class to switch the serilizer with the request parameter.

        Args:
            args (list): request parameters
            kwargs (dict): request parameters

        Returns:
            return the expected serializer according to the request parameter.
        """
        if 'detailed' in self.request.query_params:
            return RegistrationCodePatientDetailedSerializer

        return RegistrationCodePatientSerializer
