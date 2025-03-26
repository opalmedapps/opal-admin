"""This module provides views for patient settings."""
import io
from typing import Any, Dict, List, Tuple

from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

import qrcode
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView
from qrcode.image import svg

from opal.core.views import CreateUpdateView
from opal.patients.forms import ConfirmPatientForm, SearchForm, SelectSiteForm
from opal.patients.tables import PatientTable

from .models import RelationshipType, Site
from .tables import RelationshipTypeTable


class RelationshipTypeListView(SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = RelationshipType
    table_class = RelationshipTypeTable
    ordering = ['pk']
    template_name = 'patients/relationship_type/list.html'


class RelationshipTypeCreateUpdateView(CreateUpdateView):
    """
    This `CreateView` displays a form for creating an `RelationshipType` object.

    It redisplays the form with validation errors (if there are any) and saves the `RelationshipType` object.
    """

    model = RelationshipType
    template_name = 'patients/relationship_type/form.html'
    fields = [
        'name_en',
        'name_fr',
        'description_en',
        'description_fr',
        'start_age',
        'end_age',
        'form_required',
    ]
    success_url = reverse_lazy('patients:relationshiptype-list')


class RelationshipTypeDeleteView(generic.edit.DeleteView):
    """
    A view that displays a confirmation page and deletes an existing `RelationshipType` object.

    The given relationship type object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = RelationshipType
    template_name = 'patients/relationship_type/confirm_delete.html'
    success_url = reverse_lazy('patients:relationshiptype-list')


def _patient_data() -> Any:
    return {
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
                'active': True,
            },
        ],
    }


def _find_patient_by_mrn(mrn: str, site: str) -> Any:
    """
    Search patient info by MRN code.

    Args:
        mrn: Medical Record Number (MRN) code (e.g., 9999993)
        site: site code (e.g., MGH)

    Returns:
        patient info or an error in JSON format
    """
    return [{
        'first_name': _patient_data()['firstName'],
        'last_name': _patient_data()['lastName'],
        'date_of_birth': _patient_data()['dateOfBirth'],
        'card_number': _patient_data()['mrns'][0]['mrn'],
    }]


def _find_patient_by_ramq(ramq: str) -> Any:
    """
    Search patient info by RAMQ code.

    Args:
        ramq (str): RAMQ code

    Returns:
        patient info or an error in JSON format
    """
    return [{
        'first_name': _patient_data()['firstName'],
        'last_name': _patient_data()['lastName'],
        'date_of_birth': _patient_data()['dateOfBirth'],
        'card_number': _patient_data()['ramq'],
    }]


class AccessRequestView(SessionWizardView):
    """
    Form wizard view providing the steps for a caregiver's patient access request.

    The collected information is stored in the server-side session. Once all information is collected,
    a confirmation page with a QR code is displayed.
    """

    model = Site
    form_list = [
        ('site', SelectSiteForm),
        ('search', SearchForm),
        ('confirm', ConfirmPatientForm),
    ]
    template_list = {
        'site': 'patients/access_request/access_request.html',
        'search': 'patients/access_request/access_request.html',
        'confirm': 'patients/access_request/access_request.html',
    }

    def get_template_names(self) -> List[str]:
        """
        Return the template url for a step.

        Returns:
            the template url for a step
        """
        return [self.template_list[self.steps.current]]

    def process_step(self, form: Form) -> Any:
        """
        Postprocess the form data.

        Args:
            form: the form of the step being processed

        Returns:
            the raw `form.data` dictionary
        """
        form_step_data = self.get_form_step_data(form)
        if self.steps.current == 'site':
            site_selection = form_step_data['site-sites']
            self.request.session['site_selection'] = site_selection

        return form_step_data

    def get_context_data(self, form: Form, **kwargs: Any) -> Dict[str, Any]:
        """
        Return the template context for a step.

        Args:
            form: a list of different forms
            kwargs: additional keyword arguments

        Returns:
            the template context for a step
        """
        context: Dict[str, Any] = super().get_context_data(form=form, **kwargs)
        if self.steps.current == 'site':
            context.update({'header_title': _('Hospital Information')})
        elif self.steps.current == 'search':  # pragma: no cover
            context.update({'header_title': _('Patient Details')})
        elif self.steps.current == 'confirm':
            context.update({'header_title': _('Patient Details')})
            medical_card = self.get_cleaned_data_for_step(self.steps.prev)['medical_card']
            medical_number = self.get_cleaned_data_for_step(self.steps.prev)['medical_number']
            site_code = self.get_cleaned_data_for_step('site')['sites']
            if medical_card == 'mrn':
                context.update({
                    'table': PatientTable(_find_patient_by_mrn(medical_number, site_code)),
                })
            else:
                context.update({
                    'table': PatientTable(_find_patient_by_ramq(medical_number)),
                })

        return context

    def get_form_initial(self, step: str) -> dict[str, str]:
        """
        Return a dictionary which will be passed to the form for `step` as `initial`.

        If no initial data was provided while initializing the form wizard, an empty dictionary will be returned.

        Args:
            step: a form step

        Returns:
            a dictionary or an empty dictionary for a step
        """
        initial: dict[str, str] = self.initial_dict.get(step, {})
        if step == 'site' and 'site_selection' in self.request.session:
            site_user_selection = Site.objects.filter(pk=self.request.session['site_selection']).first()
            if site_user_selection:
                initial.update({
                    'sites': site_user_selection,
                })
        return initial

    def done(self, form_list: Tuple, **kwargs: Any) -> HttpResponse:
        """
        Redirect to a test qr code page.

        Args:
            form_list: a list of different forms
            kwargs: additional keyword arguments

        Returns:
            the object of HttpResponse
        """
        form_data = [form.cleaned_data for form in form_list]
        factory = svg.SvgImage
        img = qrcode.make(form_data[0]['sites'], image_factory=factory, box_size=10)
        stream = io.BytesIO()
        img.save(stream)

        return render(self.request, 'patients/access_request/test_qr_code.html', {
            'svg': stream.getvalue().decode(),
            'header_title': _('QR Code Generation'),
        })
