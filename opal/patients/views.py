"""This module provides views for patient settings."""
import io
import uuid
from collections import Counter
from datetime import date
from typing import Any, Dict, List, Tuple

from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

import qrcode
from dateutil.relativedelta import relativedelta
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView
from qrcode.image import svg

from opal.core.views import CreateUpdateView
from opal.patients import forms
from opal.services.hospital.hospital_data import OIEPatientData
from opal.users.models import Caregiver

from . import constants
from .models import CaregiverProfile, Patient, Relationship, RelationshipStatus, RelationshipType, Site
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
        ('password', forms.ConfirmPasswordForm),
    ]
    form_title_list = {
        'site': _('Hospital Information'),
        'search': _('Patient Details'),
        'confirm': _('Patient Details'),
        'relationship': _('Requestor Details'),
        'account': _('Requestor Details'),
        'requestor': _('Requestor Details'),
        'finished': _('Requestor Details'),
        'password': _('Confirm access to patient data'),
    }
    template_list = {
        'site': 'patients/access_request/access_request.html',
        'search': 'patients/access_request/access_request.html',
        'confirm': 'patients/access_request/access_request.html',
        'relationship': 'patients/access_request/access_request.html',
        'account': 'patients/access_request/access_request.html',
        'requestor': 'patients/access_request/access_request.html',
        'finished': 'patients/access_request/access_request.html',
        'password': 'patients/access_request/access_request.html',
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
            if user_type == str(constants.NEW_USER):
                form_class = forms.NewUserForm
                form = form_class(data)
                self.condition_dict = {'finished': False}
        elif step == 'password':
            user_type = self.get_cleaned_data_for_step('account')['user_type']
            if user_type == str(constants.NEW_USER):
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
        elif step == 'password':
            kwargs['authorized_user'] = self.request.user
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
        # process form data for easily accessing to
        new_form_data = self._process_form_data(form_data)
        # generate access request for both of the case(new user or existing user)
        self._generate_access_request(new_form_data)

        factory = svg.SvgImage
        img = qrcode.make(new_form_data['sites'], image_factory=factory, box_size=10)
        stream = io.BytesIO()
        img.save(stream)

        return render(self.request, 'patients/access_request/test_qr_code.html', {
            'svg': stream.getvalue().decode(),
            'header_title': _('QR Code Generation'),
        })

    def _set_relationship_start_date(self, date_of_birth: date, relationship_type: str) -> date:
        """
        Calculate the start date for the relationship record.

        Args:
            date_of_birth: patient's date of birth
            relationship_type: user selection for relationship type

        Returns:
            the start date
        """
        # Get the date 1 years ago from now
        reference_date = date.today() - relativedelta(years=constants.RELATIVE_YEAR_VALUE)
        # Calculate patient age based on reference date
        age = Patient.calculate_age(
            date_of_birth=date_of_birth,
            reference_date=reference_date,
        )
        # Get the user choice for the relationship type in the previous step
        user_select_type = RelationshipType.objects.get(name=relationship_type)
        # Return reference date if patient age is larger or otherwise return start date based on patient's age
        if age < user_select_type.start_age:
            reference_date = date_of_birth + relativedelta(years=user_select_type.start_age)
        return reference_date

    def _create_caregiver_profile(self, form_data: dict, random_username_length: int) -> dict[str, Any]:
        """
        Create caregiver user and caregiver profile instance if not exists.

        Args:
            form_data: form data
            random_username_length: the length of random username

        Returns:
            caregiver user nad caregiver profile instance dictionary
        """
        if form_data['user_type'] == str(constants.EXISTING_USER):
            # Get the Caregiver user if it exists
            caregiver_user = Caregiver.objects.get(
                email=form_data['user_email'],
                phone_number=form_data['user_phone'],
            )
        else:
            # Create a new Caregiver user
            caregiver_user = Caregiver.objects.create(
                username=uuid.uuid4().hex[:random_username_length],
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
            )

        # Check if the caregiver record exists. If not, create a new record.
        caregiver, created = CaregiverProfile.objects.get_or_create(
            user_id=caregiver_user.id,
            defaults={'user': caregiver_user},
        )
        return {
            'caregiver_user': caregiver_user,
            'caregiver': caregiver,
        }

    def _create_patient(self, form_data: dict) -> Patient:
        """
        Create patient instance if not exists.

        Args:
            form_data: form data

        Returns:
            patient instance
        """
        patient_record = form_data['patient_record']
        # Check if the patient record exists searching by RAMQ. If not, create a new record.
        patient, created = Patient.objects.get_or_create(
            ramq=patient_record.ramq,
            defaults={
                'first_name': patient_record.first_name,
                'last_name': patient_record.last_name,
                'date_of_birth': patient_record.date_of_birth,
                'sex': patient_record.sex,
                'ramq': patient_record.ramq,
            },
        )

        return patient

    def _create_relationship(   # noqa: WPS210
        self,
        form_data: dict,
        caregiver_dict: dict[str, Any],
        patient: Patient,
    ) -> None:
        """
        Create relationship instance if not exists.

        Args:
            form_data: form data
            caregiver_dict: caregiver user nad caregiver profile instance dictionary
            patient: patient instance
        """
        caregiver_user = caregiver_dict['caregiver_user']
        caregiver = caregiver_dict['caregiver']
        patient_record = form_data['patient_record']
        relationship_type = form_data['relationship_type']

        # Check if there is no relationship between requestor and patient
        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done.
        relationships = Relationship.objects.get_relationship_by_patient_caregiver(
            str(relationship_type),
            caregiver_user.first_name,
            caregiver_user.last_name,
            caregiver_user.id,
            patient_record.ramq,
        )

        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done
        # For `Self` relationship, the status is CONFIRMED
        status = RelationshipStatus.CONFIRMED if str(relationship_type) == 'Self' else RelationshipStatus.PENDING
        if not relationships:
            Relationship.objects.create(
                patient=patient,
                caregiver=caregiver,
                type=relationship_type,
                status=status,
                reason='',
                request_date=date.today(),
                start_date=self._set_relationship_start_date(
                    patient_record.date_of_birth,
                    relationship_type,
                ),
            )

    def _generate_access_request(self, new_form_data: dict) -> None:
        # Create caregiver user and caregiver profile if not exists
        caregiver_dict = self._create_caregiver_profile(new_form_data, random_username_length=constants.USERNAME_LENGTH)

        # Create patient instance if not exists
        patient = self._create_patient(new_form_data)

        # Create relationship instance if not exists
        self._create_relationship(new_form_data, caregiver_dict, patient)

    def _process_form_data(self, forms_data: list) -> dict:
        """
        Process form data for easily accessing to.

        Args:
            forms_data: a list of form data

        Returns:
            the processed form data dictionary
        """
        processed_form_date = {}
        for form_data in forms_data:
            for key, value in form_data.items():
                processed_form_date[key] = value
        return processed_form_date

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
