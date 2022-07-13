from django.http import HttpResponse

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from opal.caregivers.api.serializer import RegistrationEncryptionInfoSerializer
from opal.caregivers.models import RegistrationCode
from opal.patients.models import HospitalPatient


class GetRegistrationEncryptionInfo(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, hashcode: str) -> HttpResponse:
        patientinfo = RegistrationCode.objects.select_related('relationship').get(code=hashcode, status='NEW')
        mrns = HospitalPatient.objects.filter(patient=patientinfo.relationship.patient)
        print(mrns)
        print(patientinfo)
        return Response(patientinfo.id)
