"""This module provides views for hospital-specific settings."""
import base64
import io
import json
from collections import Counter, OrderedDict
from datetime import date
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple, Type

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from django.views.generic.base import ContextMixin, TemplateResponseMixin, View

import qrcode
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView
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
from .forms import ManageCaregiverAccessUserForm, RelationshipAccessForm
from .models import CaregiverProfile, Patient, Relationship, RelationshipStatus, RelationshipType, RoleType, Site

_StorageValue = str | dict[str, Any]


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


class NewAccessRequestView(TemplateResponseMixin, ContextMixin, View):  # noqa: WPS214 (too many methods)
    """
    View to process an access request.

    Supports multiple forms within the same view.
    The form for the current form is active.
    Any previous form (validated) is disabled.
    """

    template_name = 'patients/access_request/new_access_request.html'
    template_name_confirm = 'patients/access_request/access_request_confirm.html'
    prefix = 'search'

    forms = OrderedDict({
        'search': forms.AccessRequestSearchPatientForm,
        'patient': forms.AccessRequestConfirmPatientForm,
        'relationship': forms.AccessRequestRequestorForm,
        'confirm': forms.AccessRequestConfirmForm,
    })
    texts = {
        'search': 'Find Patient',
        'patient': 'Confirm Patient Data',
        'relationship': 'Continue',
        'confirm': 'Generate Registration Code',
    }
    current_step_name = 'current_step'
    session_key_name = 'access_request'

    def get(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """
        Handle GET requests: instantiate a blank version of the form.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response
        """
        self.request.session[self.session_key_name] = {}

        return self.render_to_response(self.get_context_data(
            search_form=forms.AccessRequestSearchPatientForm(prefix=self.prefix),
        ))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: C901, WPS210, WPS231
        """
        Handle POST requests: instantiate a form instance with the passed POST variables and then check if it's valid.

        Args:
            request: the HTTP request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            the HTTP response

        Raises:
            SuspiciousOperation: if the step is invalid
        """
        management_form = forms.AccessRequestManagementForm(request.POST)
        if not management_form.is_valid():
            raise SuspiciousOperation('ManagementForm data is missing or has been tampered with.')

        current_step = management_form.cleaned_data.get(self.current_step_name)

        if current_step and current_step in self.forms:
            next_step = current_step
            # get all current forms and validate them
            current_forms = self._get_forms(current_step)
            current_form = current_forms[-1]

            # only validate the current form since all others use stored data
            # don't continue if the next button was not clicked (e.g., an unpoly event was triggered)
            if current_form.is_valid() and 'next' in self.request.POST:
                # store data for current step in session
                self._store_form_data(current_form, current_step)
                next_step = self._next_step(current_step)

                if next_step:
                    current_form.disable_fields()  # type: ignore[attr-defined]
                    next_form_class = self.forms[next_step]
                    current_forms.append(next_form_class(**self._get_form_kwargs(next_step)))
                else:
                    # TODO: avoid resubmit via Post/Redirect/Get pattern: https://stackoverflow.com/a/6320124
                    # TODO: create relationship, patient (if new) etc.
                    return render(self.request, 'patients/access_request/qr_code.html', {
                        'qrcode': base64.b64encode(self._generate_qr_code('').getvalue()).decode(),
                    })
            else:
                print("some forms are invalid (or the next button wasn't clicked)")
                for form in current_forms:
                    print(form.errors)

            context_data = self.get_context_data(
                current_forms=current_forms,
                current_step=current_step,
                next_step=next_step,
            )

            return self.render_to_response(context_data)

        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: C901, WPS210, WPS231
        """
        Return the context data for rendering the view.

        Args:
            kwargs: additional keyword arguments

        Returns:
            a dictionary of data to be accessible by the template
        """
        context_data = super().get_context_data(**kwargs)
        current_step = kwargs.get('current_step', 'search')
        next_step = kwargs.get('next_step', 'search')
        current_forms = kwargs.get('current_forms', [])

        context_data['management_form'] = forms.AccessRequestManagementForm(initial={
            'current_step': next_step,
        })
        context_data['next_button_text'] = self.texts.get(next_step)

        for current_form in current_forms:
            prefix = self._get_prefix(current_form.__class__)
            context_data[f'{prefix}_form'] = current_form

        disable_next = False

        if len(current_forms) >= 2 and current_forms[0].is_valid():
            patient_form = current_forms[1]
            if patient_form.patient:
                patients = [patient_form.patient]
            else:
                patients = []

            disable_next = not patient_form.is_valid()

            if isinstance(patient_form.patient, Patient):
                context_data['patient_table'] = tables.PatientTable(patients)
            else:
                context_data['patient_table'] = tables.ConfirmPatientDetailsTable(patients)

        relationship_form = context_data.get('relationship_form')

        if relationship_form:
            existing_user = relationship_form.existing_user
            table_data = [existing_user] if existing_user else []
            context_data['user_table'] = tables.ExistingUserTable(table_data)

        if current_step == 'confirm' or next_step == 'confirm':
            # populate relationship type (in case it is just the ID)
            relationship_form.full_clean()
            user_type = relationship_form.cleaned_data['user_type']
            # might be helpful to use an enum like done with MedicalCard
            is_existing_user = user_type == '1'

            if is_existing_user:
                context_data['next_button_text'] = 'Submit Access Request'

        # TODO: might not be needed anymore
        context_data['next_button_disabled'] = disable_next

        return context_data

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

    def _get_prefix(self, form_class: Type[Form]) -> Optional[str]:
        """
        Return the prefix for the given form class.

        The prefix needs to be defined in the class's `form` attribute.

        Args:
            form_class: the form class

        Returns:
            the prefix for the form class, None if the form class is not present
        """
        for prefix, current_form_class in self.forms.items():
            if current_form_class == form_class:
                return prefix

        return None

    def _get_storage(self) -> dict[str, _StorageValue]:
        """
        Return the storage for this view from the user's session.

        Returns:
            the storage dictionary
        """
        storage: dict[str, _StorageValue] = self.request.session[self.session_key_name]

        return storage  # noqa: WPS331

    def _get_saved_form_data(self, step: str) -> dict[str, Any]:
        """
        Return the stored form data from the given step.

        Args:
            step: the name of the step

        Returns:
            the dictionary of form data for the given step
        """
        storage = self._get_storage()

        # the data for a step is always a dict
        return storage[f'step_{step}']  # type: ignore[return-value]

    def _store_form_data(self, form: Form, step: str) -> None:  # noqa: WPS210
        """
        Store the validated form data for the given step in the user's session.

        The form needs to be validated first.

        To support serialization to JSON in the session,
        model instances are replaced with their primary key.
        Named tuples are replaced with their dictionary representation.

        Args:
            form: the valid form
            step: the step the form is for
        """
        storage = self._get_storage()

        cleaned_data = form.cleaned_data
        for key, value in cleaned_data.items():
            # convert model instances to their primary key
            # to support serializing them to JSON
            if isinstance(value, Model):
                cleaned_data[key] = value.pk

        storage[f'step_{step}'] = cleaned_data

        if step == 'search':
            # form type is the search form which has the patient attribute
            patient = form.patient  # type: ignore[attr-defined]
            # TODO: patient could also be an actual Patient instance, need to add support
            # convert it to a dictionary to be able to serialize it into JSON
            if isinstance(patient, Patient):
                storage['patient'] = patient.pk  # type: ignore[assignment]
            else:
                data_dict = patient._asdict()  # noqa: WPS437
                data_dict['mrns'] = [mrn._asdict() for mrn in data_dict['mrns']]  # noqa: WPS437
                # use DjangoJSONEncoder which supports date/datetime
                storage['patient'] = json.dumps(data_dict, cls=DjangoJSONEncoder)

        self.request.session.modified = True

    def _get_form_kwargs(self, step: str) -> dict[str, Any]:
        """
        Return the kwargs for the form of the given step.

        Takes care of loading any required data from the session storage.

        Args:
            step: the step to get the form's kwargs for

        Returns:
            the dictionary of keyword arguments
        """
        kwargs: dict[str, Any] = {'prefix': step}
        storage = self._get_storage()

        if step in {'patient', 'relationship'}:
            # TODO: should also support a Patient instance that way
            # i.e., the patient already exists
            # TODO: might be better to refactor into a function so it can be tested easier
            patient_data: str = storage.get('patient', '[]')  # type: ignore[assignment]
            if isinstance(patient_data, int):
                patient = Patient.objects.get(pk=patient_data)
                date_of_birth = patient.date_of_birth
            else:
                patient = json.loads(patient_data)
                date_of_birth = date.fromisoformat(patient['date_of_birth'])

            if step == 'patient':
                kwargs.update({
                    'patient': patient,
                })
            else:
                kwargs.update({
                    'date_of_birth': date_of_birth,
                })
        elif step == 'confirm':
            kwargs.update({
                'username': self.request.user.username,
            })

        return kwargs

    def _get_forms(self, current_step: str) -> list[Form]:  # noqa: WPS210, WPS231
        """
        Return all forms up to the current step.

        Initialize previous (already valid forms) with data from the session storage.
        All fields for these forms are also disabled.

        The current form is initialized with the POST data from the current request.

        Args:
            current_step: the current step

        Returns:
            the list of forms
        """
        form_list = []

        for step, form_class in self.forms.items():
            # use the request data for the current step
            # otherwise, load the form data from session storage
            data = self.request.POST if step == current_step else self._get_saved_form_data(step)
            # since form fields of previous forms are disabled, initial needs to be used
            # disabled form fields ignore the data and use initial instead
            #
            # initial requires the field name without the prefix,
            # strip it from the POST data which contains keys with the prefix
            initial = {
                key.replace(f'{current_step}-', ''): value
                for key, value in data.items()
            }

            # use initial instead of data to avoid validating a form when up-validate is used
            if step == current_step and 'X-Up-Validate' in self.request.headers:
                data = {}

            form = form_class(
                # pass none instead of empty dict to not bind the form
                data=data or None,
                initial=initial,
                **self._get_form_kwargs(step),
            )

            # disable fields for all forms except the current one
            if step != current_step:
                form.disable_fields()

            form_list.append(form)

            if step == current_step:
                break

        return form_list

    def _next_step(self, current_step: str) -> Optional[str]:
        """
        Determine the next step in the process.

        Args:
            current_step: the current step name

        Returns:
            the next step name, None if the current step is the last step
        """
        keys = list(self.forms.keys())

        next_index = keys.index(current_step) + 1

        return keys[next_index] if len(keys) > next_index else None


class AccessRequestView(PermissionRequiredMixin, SessionWizardView):  # noqa: WPS214
    """
    Form wizard view providing the steps for a caregiver's patient access request.

    The collected information is stored in the server-side session. Once all information is collected,
    a confirmation page with a QR code is displayed.
    """

    model = Site
    permission_required = ('patients.can_perform_registration',)
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

    def get_context_data(self, form: Form, **kwargs: Any) -> dict[str, Any]:
        """
        Return the template context for a step.

        Args:
            form: a list of different forms
            kwargs: additional keyword arguments

        Returns:
            the template context for a step
        """
        context: dict[str, Any] = super().get_context_data(form=form, **kwargs)
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
            kwargs['ramq'] = patient_record.ramq
            kwargs['mrn'] = patient_record.mrns[0].mrn
            kwargs['site'] = patient_record.mrns[0].site
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
            code=generate_random_registration_code(settings.INSTITUTION_CODE, 10),
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
        patient.full_clean()

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
        relationship_type = form_data['relationship_type']
        # Check if there is no relationship between requestor and patient
        relationship: Optional[Relationship] = Relationship.objects.get_relationship_by_patient_caregiver(
            str(relationship_type),
            caregiver_user.id,
            patient.ramq,
        ).first()
        # For `Self` relationship, the status is CONFIRMED
        if relationship_type.role_type == RoleType.SELF:
            status = RelationshipStatus.CONFIRMED
        else:
            status = RelationshipStatus.PENDING

        start_date = Relationship.calculate_default_start_date(
            date.today(),
            patient.date_of_birth,
            relationship_type,
        )

        if not relationship:
            relationship = Relationship(
                patient=patient,
                caregiver=caregiver,
                type=relationship_type,
                status=status,
                reason='',
                request_date=date.today(),
                start_date=start_date,
                end_date=Relationship.calculate_end_date(
                    patient.date_of_birth,
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
        context: dict[str, Any],
        patient_record: OIEPatientData,
    ) -> dict[str, Any]:
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


class ManageCaregiverAccessListView(PermissionRequiredMixin, SingleTableMixin, FilterView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = Relationship
    permission_required = ('patients.can_manage_relationships',)
    table_class = tables.PendingRelationshipTable
    template_name = 'patients/relationships/pending_relationship_list.html'
    queryset = Relationship.objects.select_related(
        'patient', 'caregiver__user', 'type',
    ).prefetch_related(
        'patient__hospital_patients__site',
    )
    filterset_class = ManageCaregiverAccessFilter
    ordering = ['request_date']

    def get_filterset_kwargs(self, filterset_class: ManageCaregiverAccessFilter) -> dict[str, Any]:  # noqa: WPS615
        """
        Apply the filter arguments on the set of data.

        Args:
            filterset_class: the filter arguments

        Returns:
            the filter keyword arguments
        """
        # Only use filter query arguments for the filter to support sorting etc. with django-tables2
        # see: https://github.com/carltongibson/django-filter/issues/1521

        # Check if the query strings contain filter fields and
        # create a data dictionary of filter fields and values
        filter_fields = set(filterset_class.get_filters().keys())
        query_strings = set(self.request.GET.keys())
        data = {
            filter_field: self.request.GET.get(filter_field)
            for filter_field in filter_fields.intersection(query_strings)
        }
        filterset_kwargs: dict[str, Any] = super().get_filterset_kwargs(filterset_class)
        filterset_kwargs['data'] = data or None

        # if no filter fields are used in the query strings default to pending relationships only
        if not data:
            filterset_kwargs['queryset'] = self.queryset.filter(
                status=RelationshipStatus.PENDING,
            ).order_by('request_date')

        return filterset_kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # noqa: WPS615
        """
        Return the template context for `PendingRelationshipListView` update view.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the template context for `PendingRelationshipListView`
        """
        context_data: dict[str, Any] = super().get_context_data(**kwargs)

        filter_used = context_data['filter'].form.is_bound
        # could also reverse in the template via a custom filter or this trick: https://stackoverflow.com/a/30075273
        context_data['is_pending'] = not filter_used
        context_data['is_search'] = filter_used

        return context_data


class ManageCaregiverAccessUpdateView(PermissionRequiredMixin, UpdateView[Relationship, ModelForm[Relationship]]):
    """
    This view is to handle relationship updates and view only requests.

    It overrides `get_context_data()` to provide the correct `cancel_url` when editing a pending request.

    It overrides `get_form_kwargs()` to provide data needed for instantiating the form.
    """

    model = Relationship
    permission_required = ('patients.can_manage_relationships',)
    template_name = 'patients/relationships/edit_relationship.html'
    form_class = RelationshipAccessForm
    success_url = reverse_lazy('patients:relationships-list')
    queryset = Relationship.objects.select_related(
        'patient', 'caregiver__user', 'type',
    ).prefetch_related(
        'patient__hospital_patients__site',
    )

    permission_required = ('patients.can_manage_relationships',)
    success_url = reverse_lazy('patients:relationships-pending-list')

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Return the template context for `ManageCaregiverAccessUpdateView` update view.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the template context for `ManagePendingUpdateView`
        """
        context_data = super().get_context_data(**kwargs)
        default_success_url = reverse_lazy('patients:relationships-list')
        if self.request.method == 'POST':
            context_data['cancel_url'] = context_data['form'].cleaned_data['cancel_url']
        elif self.request.META.get('HTTP_REFERER'):
            context_data['cancel_url'] = self.request.META.get('HTTP_REFERER')
        else:
            context_data['cancel_url'] = default_success_url

        return context_data

    def get_success_url(self) -> str:  # noqa: WPS615
        """
        Provide the correct `success_url` that re-submits search query or default success_url.

        Returns:
            the success url link
        """
        success_url: str = reverse_lazy('patients:relationships-list')
        if self.request.POST.get('cancel_url', False):
            success_url = self.request.POST['cancel_url']

        return success_url

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Return a view-only page if the relationship is expired, otherwise return the edit page.

        Args:
            request: the http request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            regular response for continuing get functionlity for `ManageCaregiverAccessUpdateView`
        """
        relationship_record = self.get_object()
        http_referer = self.request.META.get('HTTP_REFERER')
        cancel_url = http_referer if http_referer else self.get_success_url()
        if relationship_record.status == RelationshipStatus.EXPIRED:
            return render(
                request,
                'patients/relationships/view_relationship.html',
                {
                    'relationship': relationship_record,
                    'cancel_url': cancel_url,
                },
            )

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Save updates for the `first_name` and `last_name` fields that are related to the caregiver/user module.

        Relationships of status expired are not allowed to post, they are redirected to view only page.

        Args:
            request: the http request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            regular response for continuing post functionality of the `ManageCaregiverAccessUpdateView`
        """
        relationship_record = self.get_object()
        # to refuse any post request when status is EXPIRED even if front-end restrictions are bypassed
        if relationship_record.status == RelationshipStatus.EXPIRED:
            return render(
                request,
                'patients/relationships/view_relationship.html',
                {
                    'relationship': relationship_record,
                    'cancel_url': self.get_success_url(),
                },
                status=HTTPStatus.METHOD_NOT_ALLOWED,
            )

        return super().post(request, **kwargs)

    def form_valid(self, form: ModelForm[Relationship]) -> HttpResponse:
        """
        Save validates user form and return valid_form only if user details are validated.

        Args:
            form: an instance of `ManageCaregiverAccessUpdateForm`

        Returns:
            HttpResponse: form_valid if user form is valid, or form_invalid if it is invalid
        """
        user_record = self.get_object().caregiver.user
        user_form = ManageCaregiverAccessUserForm(self.request.POST or None, instance=user_record)

        if user_form.is_valid():
            user_form.save()
        else:
            # to show errors and display messages on the field
            for field, _value in user_form.errors.items():
                form.add_error(field, user_form.errors.get(field))  # type: ignore[arg-type]

            return self.form_invalid(form)

        return super().form_valid(form)
