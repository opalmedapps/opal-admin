from rest_framework import status, generics
from rest_framework.response import Response
from ..models import DatabankConsent
from .serializers import DatabankConsentSerializer
from opal.caregivers.api.mixins.put_as_create import AllowPUTAsCreateMixin

class DatabankConsentView(AllowPUTAsCreateMixin, generics.GenericAPIView):
    serializer_class = DatabankConsentSerializer
    queryset = DatabankConsent.objects.all()
    lookup_field = 'patient__id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def _get_object_or_none(self):
        try:
            patient_id = self.kwargs['patient_id']
            return self.queryset.get(patient__id=patient_id)
        except DatabankConsent.DoesNotExist:
            return None
