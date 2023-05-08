"""This module provides views for hospital-specific settings."""
import base64
import io
from collections import Counter
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import Form
from django.forms.models import ModelForm
from django.http import HttpResponse, HttpResponseNotAllowed
from django.http.request import HttpRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

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
from .forms import RelationshipAccessForm, RelationshipTypeUpdateForm
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
    form_class = RelationshipTypeUpdateForm
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


class PendingRelationshipListView(PermissionRequiredMixin, SingleTableMixin, FilterView):
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


class ManageRelationshipUpdateMixin(UpdateView[Relationship, ModelForm[Relationship]]):
    """
    This is a mixin view that is inherited by `ManagePendingUpdateView` and `ManagePendingReadOnlyView`.

    It provides common features among the inherited views.
    """

    model = Relationship
    template_name = 'patients/relationships/edit_relationship.html'
    form_class = RelationshipAccessForm

    def get_form_kwargs(self) -> Dict[str, Any]:
        """
        Build the keyword arguments required to instantiate the `RelationshipAccessForm`.

        Returns:
            keyword arguments for instantiating the `RelationshipAccessForm`
        """
        kwargs = super().get_form_kwargs()

        relationship = self.object
        patient = relationship.patient
        kwargs['date_of_birth'] = patient.date_of_birth
        kwargs['relationship_type'] = relationship.type
        kwargs['request_date'] = relationship.request_date

        return kwargs


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
        context_data = super().get_context_data(**kwargs)
        default_success_url = reverse_lazy('patients:relationships-pending-list')
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
        success_url: str = reverse_lazy('patients:relationships-pending-list')
        if self.request.POST.get('cancel_url', False):
            success_url = self.request.POST['cancel_url']

        return success_url

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Save updates for the `first_name` and `last_name` fields that are related to the caregiver/user module.

        Args:
            request: the http request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            regular response for continuing post functionality of the `ManagePendingUpdateView`
        """
        relationship_record = Relationship.objects.get(pk=kwargs['pk'])
        # to refuse any post request when status is EXPIRED even if front-end restrictions are bypassed
        if relationship_record.status == RelationshipStatus.EXPIRED:
            return HttpResponseNotAllowed(['GET'])

        user_record = relationship_record.caregiver.user
        user_record.first_name = request.POST['first_name']
        user_record.last_name = request.POST['last_name']
        # TODO: run standard validations on the first/last field that are relevant to the user module.
        user_record.save()

        return super().post(request, kwargs['pk'])


class ManagePendingReadOnlyView(ManagePendingUpdateView):
    """
    This view inherits `ManageRelationshipUpdateMixin` used to update pending relationship requests.

    It is used for readonly requests and overrides `post()` to disable post functionality.
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseNotAllowed:
        """
        Disable post request for readonly pages to make sure it is not passed even if front end allows it.

        Args:
            request: the http request
            args: additional arguments
            kwargs: additional keyword arguments

        Returns:
            http not allowed response `HttpResponseNotAllowed`
        """
        post_return: HttpResponseNotAllowed = HttpResponseNotAllowed(['GET'])
        return post_return  # noqa: WPS331
