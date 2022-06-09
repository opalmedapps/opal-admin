"""This module provides views for Patients."""
import json
from array import array
from typing import Any, Dict

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView, View

from opal.hospital_settings.models import Site
from opal.patients.models import Patient, RelationshipType
from opal.users.models import Caregiver


# PATIENTS INDEX PAGE
class IndexView(TemplateView):
    """This `TemplateView` provides an index page for the Patients app."""

    template_name = 'patients/index.html'

    def get_context_data(self, **kwargs: array) -> Dict:
        """
        Return a hospital site list.

        Args:
            kwargs: Pass keyword arguments from the URLconf to the context.

        Returns:
            the hospital site lists
        """
        context = super().get_context_data(**kwargs)
        context['sites'] = Site.objects.all()
        return context


# SEARCH PATEINTS PAGE
class SearchPatientView(View):
    """This `View` provides an search patient page for the Patients app."""

    template_name = 'patients/search-patient.html'

    def post(self, request: Any) -> HttpResponse:
        """
        Get hopital site code and pass it to the seach page.

        Args:
            request: pass the HttpRequest as the argument to the view function.

        Returns:
            the object of HttpResponse
        """
        context = {'MRN': 'MRN0000011111'}
        if (request.POST['siteCode']):
            context['siteCode'] = request.POST['siteCode']
        return render(request, self.template_name, context=context)


class FetchPatientView(View):
    """This `View` provides an search patient page for the Patients app."""

    template_name = 'patients/fetch-patient.html'

    def post(self, request: Any) -> HttpResponse:
        """
        Fetch patient record by calling OIE apis.

        Args:
            request: pass the HttpRequest as the argument to the view function.

        Returns:
            the object of HttpResponse
        """
        # OIE JSON endpoint url : https://172.26.125.233/Patient/get
        if (request.POST['medicalType']):
            medicaltype = request.POST['medicalType']
        if (request.POST['medicalNo']):
            medicalno = request.POST['medicalNo']
        if (request.POST['siteCode']):
            sitecode = request.POST['siteCode']

        patient_parameters = {}
        if (medicaltype == 'ramq'):
            patient_parameters = {
                'medicareNumber': medicalno,
            }
        else:
            patient_parameters = {'mrn': medicalno, 'site': sitecode}

        patient_records = json.loads(fetch_patient_record(patient_parameters))

        print(patient_records['firstName'])
        print(patient_records['lastName'])
        print(patient_records['dateOfBirth'])
        print(patient_records['ramq'])

        return render(request, self.template_name, context=patient_records)


def fetch_patient_record(patient_parameters: Any) -> str:
    """
    Return a test data to simulate the data getting from OIE.

    Args:
        patient_parameters: pass this parameter send request to OIE apis.

    Returns:
        the object of HttpResponse
    """
    data_set = {
        'status': 'success',
        'data': {
            'dateOfBirth': '1953-01-01 00:00:00',
            'firstName': 'SANDRA',
            'lastName': 'TESTMUSEMGHPROD',
            'sex': 'F',
            'alias': '',
            'ramq': 'TESS53510111',
            'ramqExpiration': '2018-01-31 23:59:59',
            'mrns': [
                {
                    'site': 'MGH',
                    'mrn': '9999993',
                    'active': 1,
                },
            ],
        },
    }

    return json.dumps(data_set['data'])


class RequestorDetailsView(View):
    """This `ListView` provides requestor's relationship to the patient."""

    template_name = 'patients/requestor-details.html'

    def post(self, request: Any) -> HttpResponse:
        """
        Return a relationshiptype list.

        Args:
            request: pass the HttpRequest as the argument to the view function.

        Returns:
            the object of HttpResponse
        """
        context = {'relationshiptype': RelationshipType.objects.all()}
        return render(request, self.template_name, context=context)


class VerifyIdentificationView(View):
    """This `ListView` provides requestor's relationship to the patient."""

    template_name = 'patients/verify-identification.html'

    def post(self, request: Any) -> HttpResponse:
        """
        Verify the identification of the requestor.

        Args:
            request: pass the HttpRequest as the argument to the view function.

        Returns:
            the object of HttpResponse
        """
        context = {}
        if (request.POST['isRequestFilled']):
            context = {'isRequestFilled': request.POST['isRequestFilled']}

        return render(request, self.template_name, context=context)


class GenerateQRView(View):
    """This `ListView` provides generate QR code to the patient."""

    model = Patient, Caregiver
    template_name = 'patients/generate-qr.html'

    def post(self, request: Any) -> HttpResponse:
        """
        Generate the QR code.

        Args:
            request: pass the HttpRequest as the argument to the view function.

        Returns:
            the object of HttpResponse
        """
        context = {}
        if (request.POST['fName'] and request.POST['lName']):
            context = {
                'fullName': '{f_name} {l_name}'.format(f_name=request.POST['fName'], l_name=request.POST['lName']),
            }
        return render(request, self.template_name, context=context)
