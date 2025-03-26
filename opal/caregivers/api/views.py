"""This module is an API view that return the encryption value required to handle registration listener's requests."""
from django.db.models.functions import SHA512

from rest_framework.generics import RetrieveAPIView

from opal.caregivers.api.serializer import RegistrationEncryptionInfoSerializer
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus


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
