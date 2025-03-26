"""This module provides views for patient settings."""
import io
from collections import Counter
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
from opal.patients import forms
from opal.services.hospital.hospital_data import OIEPatientData

from .models import Relationship, RelationshipStatus, RelationshipType, Site
from .tables import ExistingUserTable, PatientTable, PendingRelationshipTable, RelationshipTypeTable


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


class AccessRequestView(SessionWizardView):  # noqa: WPS214
    """
    Form wizard view providing the steps for a caregiver's patient access request.

    The collected information is stored in the server-side session. Once all information is collected,
    a confirmation page with a QR code is displayed.
    """

    model = Site
    form_list = [
        ('site', forms.SelectSiteForm),
        ('search', forms.SearchForm),
        ('confirm', forms.ConfirmPatientForm),
        ('relationship', forms.RequestorDetailsForm),
        ('account', forms.RequestorAccountForm),
        ('requestor', forms.ExistingUserForm),
        ('finished', forms.ConfirmExistingUserForm),
    ]
    form_title_list = {
        'site': _('Hospital Information'),
        'search': _('Patient Details'),
        'confirm': _('Patient Details'),
        'relationship': _('Requestor Details'),
        'account': _('Requestor Details'),
        'requestor': _('Requestor Details'),
        'finished': _('Requestor Details'),
    }
    template_list = {
        'site': 'patients/access_request/access_request.html',
        'search': 'patients/access_request/access_request.html',
        'confirm': 'patients/access_request/access_request.html',
        'relationship': 'patients/access_request/access_request.html',
        'account': 'patients/access_request/access_request.html',
        'requestor': 'patients/access_request/access_request.html',
        'finished': 'patients/access_request/access_request.html',
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
        if self.steps.current == 'confirm':
            context = self._update_patient_confirmation_context(context)
        if self.steps.current == 'finished':
            user_record = self.get_cleaned_data_for_step(self.steps.prev)['user_record']
            context.update({'table': ExistingUserTable([user_record])})
        context.update({'header_title': self.form_title_list[self.steps.current]})
        return context

    def get_form(self, step: str = None, data: Any = None, files: Any = None) -> Any:
        """
        Initialize the form for a given `step`.

        Args:
            step: a form step
            data: form `data` argument
            files: form `files` argument

        Returns:
            the form
        """
        form = super().get_form(step, data, files)
        if step is None:
            step = self.steps.current

        if step == 'requestor':
            user_type = self.get_cleaned_data_for_step('account')['user_type']
            # If new user is selected, the current form will be replaced by `NewUserForm`.
            # The last step `finished` will be ignored.
            if user_type == '0':
                form_class = forms.NewUserForm
                form = form_class(data)
                self.condition_dict = {'finished': False}
        return form

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
        elif step == 'search' and 'site_selection' in self.request.session:
            site_code = Site.objects.get(pk=self.request.session['site_selection']).code
            if site_code:
                initial.update({
                    'site_code': site_code,
                })
        return initial

    def get_form_kwargs(self, step: str) -> dict[str, str]:
        """
        Return the keyword arguments for instantiating the form on the given step.

        Args:
            step: a form step

        Returns:
            a dictionary or an empty dictionary for a step
        """
        kwargs = {}
        if step == 'relationship':
            patient_record = self.get_cleaned_data_for_step('search')['patient_record']
            kwargs['date_of_birth'] = patient_record.date_of_birth
        elif step == 'requestor':
            relationship_type = self.get_cleaned_data_for_step('relationship')['relationship_type']
            kwargs['relationship_type'] = relationship_type
            patient_record = self.get_cleaned_data_for_step('search')['patient_record']
            kwargs['patient_record'] = patient_record
        return kwargs

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

    def _has_multiple_mrns_with_same_site_code(self, patient_record: OIEPatientData) -> bool:
        """
        Check if the number of MRN records with the same site code is greater than 1.

        Args:
            patient_record: patient record search by RAMQ or MRN

        Returns:
            True if the number of MRN records with the same site code is greater than 1
        """
        mrns = patient_record.mrns
        key_counts = Counter(mrn_dict.site for mrn_dict in mrns)
        return any(count > 1 for (site, count) in key_counts.items())

    def _update_patient_confirmation_context(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update the context for patient confirmation form.

        Args:
            context: the template context for step 'confirm'

        Returns:
            the template context for step 'confirm'
        """
        patient_record = self.get_cleaned_data_for_step(self.steps.prev)['patient_record']
        if self._has_multiple_mrns_with_same_site_code(patient_record):
            context.update({
                'error_message': _('Please note multiple MRNs need to be merged by medical records.'),
            })

        context.update({'table': PatientTable([patient_record])})
        return context


class PendingRelationshipListView(SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = Relationship
    table_class = PendingRelationshipTable
    ordering = ['request_date']
    template_name = 'patients/relationships/pending/list.html'
    queryset = Relationship.objects.filter(status=RelationshipStatus.PENDING)
