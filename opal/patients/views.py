"""This module provides views for hospital-specific settings."""
import io
from collections import Counter
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

import qrcode
from dateutil.relativedelta import relativedelta
from django_tables2 import MultiTableMixin, SingleTableView
from formtools.wizard.views import SessionWizardView
from qrcode.image import svg

from opal.caregivers.models import RegistrationCode
from opal.core.utils import generate_random_registration_code, generate_random_uuid
from opal.core.views import CreateUpdateView, UpdateView
from opal.patients import forms
from opal.services.hospital.hospital_data import OIEPatientData
from opal.users.models import Caregiver

from . import constants
from .forms import ManageCaregiverAccessForm, RelationshipPendingAccessForm, RelationshipTypeUpdateForm
from .models import CaregiverProfile, Patient, Relationship, RelationshipStatus, RelationshipType, Site
from .tables import (
    ExistingUserTable,
    PatientTable,
    PendingRelationshipTable,
    RelationshipCaregiverTable,
    RelationshipPatientTable,
    RelationshipTypeTable,
)


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
    form_class = RelationshipTypeUpdateForm
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
        ('existing', forms.ConfirmExistingUserForm),
        ('password', forms.ConfirmPasswordForm),
    ]
    form_title_list = {
        'site': _('Hospital Information'),
        'search': _('Patient Details'),
        'confirm': _('Patient Details'),
        'relationship': _('Requestor Details'),
        'account': _('Requestor Details'),
        'requestor': _('Requestor Details'),
        'existing': _('Requestor Details'),
        'password': _('Confirm access to patient data'),
    }
    template_list = {
        'site': 'patients/access_request/access_request.html',
        'search': 'patients/access_request/access_request.html',
        'confirm': 'patients/access_request/access_request.html',
        'relationship': 'patients/access_request/access_request.html',
        'account': 'patients/access_request/access_request.html',
        'requestor': 'patients/access_request/access_request.html',
        'existing': 'patients/access_request/access_request.html',
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
            patient_record = self.get_cleaned_data_for_step(self.steps.prev)['patient_record']
            context = self._update_patient_confirmation_context(context, patient_record)
        if self.steps.current == 'existing':
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
            # The step `existing` will be ignored.
            if user_type == str(constants.NEW_USER):
                form_class = forms.NewUserForm
                form = form_class(data=data, prefix=self.get_form_prefix(step, form_class))
                self.condition_dict = {'existing': False}
        # Since `form_list` will be initalized for each step,
        # the step `existing` will be ignored one more time in step `password` if the new user is selected
        elif step == 'password':
            user_type = self.get_cleaned_data_for_step('account')['user_type']
            if user_type == str(constants.NEW_USER):
                self.condition_dict = {'existing': False}
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
        initial: dict[str, Any] = self.initial_dict.get(step, {})
        if step == 'site' and 'site_selection' in self.request.session:
            site_user_selection = Site.objects.filter(pk=self.request.session['site_selection']).first()
            if site_user_selection:
                initial.update({
                    'sites': site_user_selection,
                })
        elif step == 'search' and 'site_selection' in self.request.session:
            site_user_selection = Site.objects.filter(pk=self.request.session['site_selection']).first()
            if site_user_selection:
                initial.update({
                    'site_code': site_user_selection.code,
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
        relationship = self._generate_access_request(new_form_data)
        # get a random registration code
        registration_code = generate_random_registration_code(constants.REGISTRATION_CODE_LENGTH)
        # create the registration code instance for the relationship
        RegistrationCode.objects.get_or_create(relationship=relationship, code=registration_code)
        # generate QR code for Opal registration system
        stream = self._generate_qr_code(registration_code)

        return render(self.request, 'patients/access_request/qr_code.html', {
            'svg': stream.getvalue().decode(),
            'header_title': _('QR Code Generation'),
        })

    def _generate_qr_code(self, registration_code: str) -> io.BytesIO:
        """
        Generate a QR code for Opal registration system.

        Args:
            registration_code: registration code

        Returns:
            a stream of in-memory bytes for a QR-code image
        """
        factory = svg.SvgImage
        img = qrcode.make(
            '{0}/#!/?code={1}'.format(settings.OPAL_USER_REGISTRATION_URL, registration_code),
            image_factory=factory,
            box_size=constants.QR_CODE_BOX_SIZE,
        )
        stream = io.BytesIO()
        img.save(stream)
        return stream

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
        user_select_type = RelationshipType.objects.filter(name=relationship_type).first()
        # Return reference date if patient age is larger or otherwise return start date based on patient's age
        if user_select_type and age < user_select_type.start_age:
            reference_date = date_of_birth + relativedelta(years=user_select_type.start_age)
        return reference_date

    def _create_caregiver_profile(self, form_data: dict, random_username_length: int) -> dict[str, Any]:
        """
        Create caregiver user and caregiver profile instance if not exists.

        Args:
            form_data: form data
            random_username_length: the length of random username

        Returns:
            caregiver user and caregiver profile instance dictionary
        """
        caregiver_dict: dict[str, Any] = {}
        if form_data['user_type'] == str(constants.EXISTING_USER):
            # Get the Caregiver user if it exists
            caregiver_user = Caregiver.objects.filter(
                email=form_data['user_email'],
                phone_number=form_data['user_phone'],
            ).first()
        else:
            # Create a new Caregiver user
            caregiver_user = Caregiver.objects.create(
                username=generate_random_uuid(random_username_length),
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
            )

        # Check if the caregiver record exists. If not, create a new record.
        if caregiver_user:
            caregiver, created = CaregiverProfile.objects.get_or_create(
                user_id=caregiver_user.id,
                defaults={'user': caregiver_user},
            )
            caregiver_dict['caregiver_user'] = caregiver_user
            caregiver_dict['caregiver'] = caregiver

        return caregiver_dict

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
    ) -> Relationship:
        """
        Create relationship instance if not exists.

        Args:
            form_data: form data
            caregiver_dict: caregiver user nad caregiver profile instance dictionary
            patient: patient instance

        Returns:
            relationship instance
        """
        caregiver_user = caregiver_dict['caregiver_user']
        caregiver = caregiver_dict['caregiver']
        patient_record = form_data['patient_record']
        relationship_type = form_data['relationship_type']
        # Check if there is no relationship between requestor and patient
        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done.
        relationship: Optional[Relationship] = Relationship.objects.get_relationship_by_patient_caregiver(
            str(relationship_type),
            caregiver_user.id,
            patient_record.ramq,
        ).first()
        # TODO: we'll need to change the 'Self' once ticket QSCCD-645 is done
        # For `Self` relationship, the status is CONFIRMED
        status = RelationshipStatus.CONFIRMED if str(relationship_type) == 'Self' else RelationshipStatus.PENDING
        if not relationship:
            relationship = Relationship(
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
            relationship.full_clean()
            relationship.save()

        return relationship

    def _generate_access_request(self, new_form_data: dict) -> Relationship:
        """
        Generate the relationship instance.

        Args:
            new_form_data: processed form data

        Returns:
            relationship instance
        """
        # Create caregiver user and caregiver profile if not exists
        caregiver_dict = self._create_caregiver_profile(new_form_data, random_username_length=constants.USERNAME_LENGTH)

        # Create patient instance if not exists
        patient = self._create_patient(new_form_data)

        # Create relationship instance if not exists
        return self._create_relationship(new_form_data, caregiver_dict, patient)

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
        patient_record: OIEPatientData,
    ) -> Dict[str, Any]:
        """
        Update the context for patient confirmation form.

        Args:
            context: the template context for step 'confirm'
            patient_record: patient record search by RAMQ or MRN

        Returns:
            the template context for step 'confirm'
        """
        if self._has_multiple_mrns_with_same_site_code(patient_record):
            context.update({
                'error_message': _('Please note multiple MRNs need to be merged by medical records.'),
            })

        context.update({'table': PatientTable([patient_record])})
        return context


class PendingRelationshipListView(PermissionRequiredMixin, SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = Relationship
    permission_required = ('patients.can_manage_relationships',)
    table_class = PendingRelationshipTable
    ordering = ['request_date']
    template_name = 'patients/relationships/pending/list.html'
    queryset = Relationship.objects.filter(status=RelationshipStatus.PENDING)


class PendingRelationshipUpdateView(PermissionRequiredMixin, UpdateView):
    """
    This `UpdatesView` displays a form for updating a `Relationship` object.

    It redisplays the form with validation errors (if there are any) and saves the `Relationship` object.
    """

    model = Relationship
    permission_required = ('patients.can_manage_relationships',)
    template_name = 'patients/relationships/pending/form.html'
    form_class = RelationshipPendingAccessForm
    success_url = reverse_lazy('patients:relationships-pending-list')


class CaregiverAccessView(MultiTableMixin, generic.FormView):
    """This view provides a page that lists all caregivers for a specific patient."""

    tables = [
        RelationshipPatientTable,
        RelationshipCaregiverTable,
    ]
    # TODO: remove Relationship.objects.all(), currently it returns data for testing purposes
    # TODO: use Relationship.objects.none()
    tables_data = [
        Relationship.objects.all(),
        Relationship.objects.all(),
    ]
    template_name = 'patients/relationships-search/form.html'
    form_class = ManageCaregiverAccessForm
    success_url = reverse_lazy('patients:caregiver-access')
