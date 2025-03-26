"""This module provides views for hospital-specific settings."""
import base64
import io
import json
from collections import Counter, OrderedDict
from datetime import date
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, QuerySet
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

import qrcode
from dateutil.relativedelta import relativedelta
from django_filters.views import FilterView
from django_tables2 import MultiTableMixin, SingleTableView
from formtools.wizard.views import SessionWizardView
from qrcode.image import svg

from opal.caregivers.models import RegistrationCode
from opal.core.utils import generate_random_registration_code, generate_random_uuid
from opal.core.views import CreateUpdateView, UpdateView
from opal.patients import forms, tables
from opal.services.hospital.hospital_data import OIEPatientData
from opal.users.models import Caregiver

from . import constants
from .filters import ManageCaregiverAccessFilter
from .forms import RelationshipAccessForm
from .models import CaregiverProfile, Patient, Relationship, RelationshipStatus, RelationshipType, RoleType, Site


class RelationshipTypeListView(PermissionRequiredMixin, SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = RelationshipType
    permission_required = ('patients.can_manage_relationshiptypes',)
    table_class = tables.RelationshipTypeTable
    ordering = ['pk']
    template_name = 'patients/relationship_type/list.html'


class RelationshipTypeCreateUpdateView(PermissionRequiredMixin, CreateUpdateView[RelationshipType]):
    """
    This `CreateView` displays a form for creating an `RelationshipType` object.

    It redisplays the form with validation errors (if there are any) and saves the `RelationshipType` object.
    """

    model = RelationshipType
    permission_required = ('patients.can_manage_relationshiptypes',)
    template_name = 'patients/relationship_type/form.html'
    form_class = forms.RelationshipTypeUpdateForm
    success_url = reverse_lazy('patients:relationshiptype-list')


class RelationshipTypeDeleteView(
    PermissionRequiredMixin, generic.edit.DeleteView[RelationshipType, ModelForm[RelationshipType]],
):
    """
    A view that displays a confirmation page and deletes an existing `RelationshipType` object.

    The given relationship type object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    # see: https://github.com/typeddjango/django-stubs/issues/1227#issuecomment-1311472749
    object: RelationshipType  # noqa: A003
    model = RelationshipType
    permission_required = ('patients.can_manage_relationshiptypes',)
    template_name = 'patients/relationship_type/confirm_delete.html'
    success_url = reverse_lazy('patients:relationshiptype-list')


class NewAccessRequestView(TemplateResponseMixin, ContextMixin, View):
    template_name = 'patients/access_request/new_access_request.html'
    prefix = 'search'

    forms = OrderedDict({
        'search': forms.NewAccessRequestForm,
        'patient': forms.AccessRequestConfirmPatientForm,
        'relationship': forms.RequestorDetailsForm,
        'confirm': forms.ConfirmPasswordForm,
    })
    texts = {
        'search': 'Find Patient',
        'patient': 'Confirm Patient Data',
        'relationship': 'Continue',
        'confirm': 'Confirm',
    }
    _current_step_name = 'current_step'
    _session_key_name = 'access_request'

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
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            image_factory=factory,
            box_size=constants.QR_CODE_BOX_SIZE,
        )
        stream = io.BytesIO()
        img.save(stream)

        return stream

    def get_the_prefix(self, form_class: Type[Form]) -> Optional[str]:
        for prefix, current_form_class in self.forms.items():
            if current_form_class == form_class:
                return prefix

        return None

    def get_storage(self) -> dict[str, Union[str, dict[str, Any]]]:
        storage: dict[str, dict[str, Any]] = self.request.session[self._session_key_name]

        return storage

    def get_saved_form_data(self, step: str) -> dict[str, Any]:
        storage = self.get_storage()

        print(f'getting stored form data for {step}')

        data = storage[f'step_{step}']

        # return {
        #     f'{step}-{key}': value
        #     for key, value in data.items()
        # }
        return data

    def store_form_data(self, form: Form, step: str) -> None:
        storage = self.get_storage()

        cleaned_data = form.cleaned_data
        for key, value in cleaned_data.items():
            # convert model instances to their primary key
            # to support serializing them to JSON
            if isinstance(value, Model):
                cleaned_data[key] = value.pk

        storage[f'step_{step}'] = cleaned_data

        if step == 'search':
            patient = form.patient
            # convert it to a dictionary to be able to serialize it into JSON
            data_dict = patient._asdict()
            data_dict['mrns'] = [mrn._asdict() for mrn in data_dict['mrns']]
            storage['patient'] = json.dumps(data_dict, cls=DjangoJSONEncoder)

        self.request.session.modified = True

    def get_form_kwargs(self, current_step: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {'prefix': current_step}
        storage = self.get_storage()

        if current_step == 'patient':
            patient_data: str = storage.get('patient', '[]')  # type: ignore[assignment]
            patient = json.loads(patient_data)

            kwargs.update({
                'patient': patient,
            })
        elif current_step == 'relationship':
            patient_json: str = storage.get('patient', '[]')  # type: ignore[assignment]
            patient = json.loads(patient_json)
            kwargs.update({
                'date_of_birth': date.fromisoformat(patient['date_of_birth']),
            })

        return kwargs

    def get_forms(self, current_step: str) -> list[Form]:
        form_list = []
        for step, form_class in self.forms.items():
            data = self.request.POST if step == current_step else self.get_saved_form_data(step)
            # initial needs to be the data to make previous forms (with disabled fields) valid (validation then uses the initial data)
            initial = data

            # use initial instead of data to avoid validating a form when up-validate is used
            # if step == current_step and 'X-Up-Validate' in self.request.headers:
            #     data = None
            #     initial = {
            #         key.replace(f'{current_step}-', ''): value
            #         for key, value in self.request.POST.items()

            #     }

            disable_fields = step != current_step
            form = form_class(data=data, initial=initial, **self.get_form_kwargs(step))

            if disable_fields:
                form.disable_fields()
            form_list.append(form)
            if step == current_step:
                break

        return form_list

    def next_step(self, current_step: str) -> Optional[str]:
        keys = list(self.forms.keys())

        next_index = keys.index(current_step) + 1

        return keys[next_index] if len(keys) > next_index else None

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """Handle GET requests: instantiate a blank version of the form."""
        self.request.session[self._session_key_name] = {}

        return self.render_to_response(self.get_context_data(search_form=forms.NewAccessRequestForm(prefix=self.prefix)))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        management_form = forms.AccessRequestManagementForm(request.POST)
        if not management_form.is_valid():
            raise SuspiciousOperation(_('ManagementForm data is missing or has been tampered with.'))

        current_step = management_form.cleaned_data.get(self._current_step_name)

        if current_step and current_step in self.forms:
            next_step = current_step
            # get all current forms and validate them
            current_forms = self.get_forms(current_step)

            if all(form.is_valid() for form in current_forms):
                # store data for current step in session
                current_form = current_forms[-1]
                self.store_form_data(current_form, current_step)
                current_form.disable_fields(current_form.cleaned_data)

                next_step = self.next_step(current_step)

                if next_step:
                    next_form_class = self.forms[next_step]
                    current_forms.append(next_form_class(**self.get_form_kwargs(next_step)))
                else:
                    # TODO: avoid resubmit via Post/Redirect/Get pattern: https://stackoverflow.com/a/6320124
                    return render(self.request, 'patients/access_request/qr_code.html', {
                        'qrcode': base64.b64encode(self._generate_qr_code('').getvalue()).decode(),
                        'header_title': _('New Access Request: Success'),
                    })
            else:
                print('some forms are invalid')
                for form in current_forms:
                    print(form.errors)

            context_data = self.get_context_data(
                current_forms=current_forms,
                current_step=current_step,
                next_step=next_step,
            )

            return self.render_to_response(context_data)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context_data = super().get_context_data(**kwargs)
        current_step = kwargs.get('current_step', 'search')
        next_step = kwargs.get('next_step', 'search')
        current_forms = kwargs.get('current_forms', [])

        context_data['management_form'] = forms.AccessRequestManagementForm(initial={
            'current_step': next_step,
        })

        for current_form in current_forms:
            prefix = self.get_the_prefix(current_form.__class__)
            context_data[f'{prefix}_form'] = current_form

        disable_next = False

        if len(current_forms) >= 2 and current_forms[0].is_valid():
            patient_form = current_forms[1]
            if patient_form.patient:
                patients = [patient_form.patient]
            else:
                patients = []

            disable_next = not patient_form.is_valid()

            context_data['patient_table'] = tables.PatientTable(patients)

        context_data['next_button_text'] = self.texts.get(next_step)
        context_data['next_button_disabled'] = disable_next

        return context_data


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
            context.update({'table': tables.ExistingUserTable([user_record])})
        context.update({'header_title': self.form_title_list[self.steps.current]})
        return context

    def get_form(self, step: Optional[str] = None, data: Any = None, files: Any = None) -> Any:
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
        elif step == 'requestor':
            relationship_type = self.get_cleaned_data_for_step('relationship')['relationship_type']
            kwargs['relationship_type'] = relationship_type
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
        # create the registration code instance for the relationship and validate the registration code
        registration_code = RegistrationCode(
            relationship=relationship,
            code=generate_random_registration_code(settings.INSTITUTION_CODE, constants.REGISTRATION_CODE_LENGTH),
        )
        registration_code.full_clean()
        registration_code.save()
        # generate QR code for Opal registration system
        stream = self._generate_qr_code(registration_code.code)

        return render(self.request, 'patients/access_request/qr_code.html', {
            'qrcode': base64.b64encode(stream.getvalue()).decode(),
            'patient': relationship.patient,
            'hospital': new_form_data['sites'],
            'registration_code': registration_code,
            'registration_url': str(settings.OPAL_USER_REGISTRATION_URL),
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

    def _set_relationship_start_date(self, date_of_birth: date, relationship_type: RelationshipType) -> date:
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
        # Return reference date if patient age is larger or otherwise return start date based on patient's age
        if age < relationship_type.start_age:
            reference_date = date_of_birth + relativedelta(years=relationship_type.start_age)
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
        relationship: Optional[Relationship] = Relationship.objects.get_relationship_by_patient_caregiver(
            str(relationship_type),
            caregiver_user.id,
            patient_record.ramq,
        ).first()
        # For `Self` relationship, the status is CONFIRMED
        if relationship_type.role_type == RoleType.SELF:
            status = RelationshipStatus.CONFIRMED
        else:
            status = RelationshipStatus.PENDING

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

    def _is_searched_patient_deceased(self, patient_record: OIEPatientData) -> bool:
        """
        Check if the searched patient is deceased.

        Args:
            patient_record: patient record search by RAMQ or MRN

        Returns:
            True if the searched patient is deceased
        """
        return patient_record.deceased

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
        if self._is_searched_patient_deceased(patient_record):
            context.update({
                'error_message': _('Unable to complete action with this patient. Please contact Medical Records.'),
            })

        elif self._has_multiple_mrns_with_same_site_code(patient_record):
            context.update({
                'error_message': _('Please note multiple MRNs need to be merged by medical records.'),
            })

        context.update({
            'table': tables.ConfirmPatientDetailsTable([patient_record]),
        })
        return context


class PendingRelationshipListView(PermissionRequiredMixin, SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = Relationship
    permission_required = ('patients.can_manage_relationships',)
    table_class = tables.PendingRelationshipTable
    ordering = ['request_date']
    template_name = 'patients/relationships/pending_relationship_list.html'
    queryset = Relationship.objects.filter(status=RelationshipStatus.PENDING)


class ManageRelationshipUpdateMixin(UpdateView[Relationship, ModelForm[Relationship]]):
    """
    This is a mixin view that is inherited by `ManagePendingUpdateView` and `ManageSearchUpdateView`.

    It provides common features among the inherited views.
    """

    model = Relationship
    template_name = 'patients/relationships/edit_relationship.html'
    form_class = RelationshipAccessForm


class ManagePendingUpdateView(PermissionRequiredMixin, ManageRelationshipUpdateMixin):
    """
    This view inherits `ManageRelationshipUpdateMixin` used to update pending relationship requests.

    It overrides `get_context_data()` to provide the correct `cancel_url` when editing a pending request.
    """

    permission_required = ('patients.can_manage_relationships',)
    success_url = reverse_lazy('patients:relationships-pending-list')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Return the template context for `ManagePendingUpdateView` update view.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the template context for `ManagePendingUpdateView`
        """
        context = super().get_context_data(**kwargs)
        # to pass url to crispy form to be able to use it as a url for cancel button.
        context['cancel_url'] = reverse_lazy('patients:relationships-pending-list')

        return context


class ManageSearchUpdateView(ManageRelationshipUpdateMixin):
    """
    This view inherits `ManageRelationshipUpdateMixin` used to update a record in search access requests results.

    It overrides `get_context_data()` to provide the correct `cancel_url` when editing a pending request.

    It overrides `get_success_url()` to provide the correct `success_url` when saving an update.
    """

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Return the template context for `ManageSearchUpdateView` update view.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the template context for `ManageSearchUpdateView`
        """
        context = super().get_context_data(**kwargs)
        # to pass url to crispy form to be able to re-use the same form for different purposes
        default_success_url = reverse_lazy('patients:relationships-search-list')
        referrer = self.request.META.get('HTTP_REFERER')
        # to maintain the value of `cancel_url` when there is a validation error
        if context['view'].request.method == 'POST':
            context['cancel_url'] = context['form'].cleaned_data['cancel_url']
        # provide previous link with parameters to update on clicking cancel button
        elif referrer:
            context['cancel_url'] = referrer
        else:
            context['cancel_url'] = default_success_url
        return context

    def get_success_url(self) -> Any:  # noqa: WPS615
        """
        Provide the correct `success_url` that re-submits search query or default success_url.

        Returns:
            the success url link
        """
        if self.request.POST.get('cancel_url', False):
            return self.request.POST['cancel_url']

        return reverse_lazy('patients:relationships-search-list')


# The order of `MultiTableMixin` and `FilterView` classes is important!
# Otherwise the tables and filter won't be accessible form the context (e.g., in the template)
class CaregiverAccessView(MultiTableMixin, FilterView):
    """This view provides a page that lists all caregivers for a specific patient."""

    queryset = Patient.objects.prefetch_related(
        'hospital_patients__site',
        'relationships__caregiver__user',
    )
    filterset_class = ManageCaregiverAccessFilter
    tables = [tables.PatientTable, tables.RelationshipCaregiverTable]
    success_url = reverse_lazy('patients:relationships-search-list')
    template_name = 'patients/relationships/relationship_filter.html'

    def get_tables_data(self) -> List[QuerySet[Any]]:
        """
        Get tables data based on the given filter values.

        No data returned if it is initial request.

        Returns:
            Filtered list of `table_data` that should be used to populate each table
        """
        if self.filterset.is_valid():
            # Get patient's relationships
            patient = self.filterset.qs.first()
            relationships = patient.relationships.all() if patient else Relationship.objects.none()
            # Provide data for the PatientTable and RelationshipCaregiverTable tables respectively
            return [
                self.filterset.qs,
                relationships,
            ]

        return [
            Patient.objects.none(),
            Relationship.objects.none(),
        ]
