from rest_framework.generics import RetrieveAPIView

from opal.caregivers.api.serializer import RegistrationEncryptionInfoSerializer
from opal.caregivers.models import RegistrationCode


class GetRegistrationEncryptionInfo(RetrieveAPIView):
    queryset = RegistrationCode.objects.all()
    serializer_class = RegistrationEncryptionInfoSerializer
    lookup_field = 'code'
