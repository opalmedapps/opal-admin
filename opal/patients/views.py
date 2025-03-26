"""This module provides views for hospital-specific settings."""
import base64
import json
from collections import OrderedDict
from datetime import date
from http import HTTPStatus
from typing import Any, Dict, Optional, Type

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

from django_filters.views import FilterView
from django_tables2 import SingleTableMixin, SingleTableView

from opal.caregivers.models import CaregiverProfile
from opal.core.utils import qr_code
from opal.core.views import CreateUpdateView, UpdateView
from opal.patients import forms, tables
from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData

from .filters import ManageCaregiverAccessFilter
from .forms import ManageCaregiverAccessUserForm, RelationshipAccessForm
from .models import Patient, Relationship, RelationshipStatus, RelationshipType
from .utils import create_access_request

# TODO: consider changing this to a TypedDict
_StorageValue = int | str | dict[str, Any]


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


class NewAccessRequestView(  # noqa: WPS214, WPS215 (too many methods, too many base classes)
    PermissionRequiredMixin,
    TemplateResponseMixin,
    ContextMixin,
    View,
):
    """
    View to process an access request.

    Supports multiple forms within the same view.
    The form for the current form is active.
    Any previous form (validated) is disabled.
    """

    permission_required = ('patients.can_perform_registration',)
    template_name = 'patients/access_request/new_access_request.html'
    template_name_confirmation_code = 'patients/access_request/confirmation_code.html'
    template_name_confirmation = 'patients/access_request/confirmation.html'
    prefix = 'search'

    forms = OrderedDict({
        'search': forms.AccessRequestSearchPatientForm,
        'patient': forms.AccessRequestConfirmPatientForm,
        'relationship': forms.AccessRequestRequestorForm,
        'confirm': forms.AccessRequestConfirmForm,
    })
    texts = {
        'search': _('Find Patient'),
        'patient': _('Confirm Patient Data'),
        'relationship': _('Continue'),
        'confirm': _('Generate Registration Code'),
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

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # noqa: WPS210
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
                    current_forms.append(next_form_class(**self._get_form_kwargs(next_step, is_current=True)))
                else:
                    return self._done(current_forms)

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
            table_data = [existing_user.user] if existing_user else []
            context_data['user_table'] = tables.ExistingUserTable(table_data)

        if current_step == 'confirm' or next_step == 'confirm':
            # populate relationship type (in case it is just the ID)
            relationship_form.full_clean()

            if relationship_form.is_existing_user_selected(relationship_form.cleaned_data):
                context_data['next_button_text'] = _('Create Access Request')

        # TODO: might not be needed anymore
        context_data['next_button_disabled'] = disable_next

        return context_data

    def _done(self, current_forms: list[Form]) -> HttpResponse:  # noqa: WPS210 (too many local variables)
        patient_form: forms.AccessRequestConfirmPatientForm = current_forms[1]  # type: ignore[assignment]
        patient = patient_form.patient

        relationship_form: forms.AccessRequestRequestorForm = current_forms[2]  # type: ignore[assignment]
        # populate relationship type (in case it is just the ID)
        relationship_form.full_clean()

        caregiver = (
            relationship_form.existing_user
            or (relationship_form.cleaned_data['first_name'], relationship_form.cleaned_data['last_name'])
        )

        relationship, registration_code = create_access_request(
            patient=patient,
            caregiver=caregiver,
            relationship_type=relationship_form.cleaned_data['relationship_type'],
        )

        context: dict[str, Any] = {
            'relationship': relationship,
            'patient': relationship.patient,
            'requestor': relationship.caregiver,
        }
        template_name = self.template_name_confirmation

        if registration_code:
            code_url = f'{settings.OPAL_USER_REGISTRATION_URL}/#!code={registration_code.code}'
            context.update({
                'registration_url': code_url,
                'registration_code': registration_code.code,
                'qr_code': base64.b64encode(qr_code(code_url)).decode(),
            })
            template_name = self.template_name_confirmation_code

        # TODO: avoid resubmit via Post/Redirect/Get pattern: https://stackoverflow.com/a/6320124
        return render(self.request, template_name, context)

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

    def _store_form_data(  # noqa: C901, WPS210 (too complex, too many local variables)
        self,
        form: Form,
        step: str,
    ) -> None:
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
            # TODO: refactor into a patient_to_json function
            # form type is the search form which has the patient attribute
            patient = form.patient  # type: ignore[attr-defined]
            if isinstance(patient, Patient):
                storage['patient'] = patient.pk
            else:
                # convert it to a dictionary to be able to serialize it into JSON
                data_dict = patient._asdict()  # noqa: WPS437
                data_dict['mrns'] = [mrn._asdict() for mrn in data_dict['mrns']]  # noqa: WPS437
                # use DjangoJSONEncoder which supports date/datetime
                storage['patient'] = json.dumps(data_dict, cls=DjangoJSONEncoder)
        elif step == 'relationship':
            caregiver: Optional[CaregiverProfile] = form.existing_user  # type: ignore[attr-defined]

            if caregiver:
                storage['caregiver'] = caregiver.pk

        self.request.session.modified = True

    def _get_form_kwargs(  # noqa: C901, WPS210 (too complex, too many local variables)
        self,
        step: str,
        is_current: bool,
    ) -> dict[str, Any]:
        """
        Return the kwargs for the form of the given step.

        Takes care of loading any required data from the session storage.

        Args:
            step: the step to get the form's kwargs for
            is_current: whether the step is the current step

        Returns:
            the dictionary of keyword arguments
        """
        kwargs: dict[str, Any] = {}

        # only add prefix to the current/active form
        # this avoids the form field values to return None as their value for previous forms
        # e.g., form['card_type].value()
        if is_current:
            kwargs.update({'prefix': step})

        storage = self._get_storage()

        if step in {'patient', 'relationship'}:
            # TODO: might be better to refactor into a function so it can be tested easier
            patient_data: str = storage.get('patient', '[]')  # type: ignore[assignment]
            if isinstance(patient_data, int):
                patient = Patient.objects.get(pk=patient_data)
            else:
                patient_json = json.loads(patient_data)
                date_of_birth = date.fromisoformat(patient_json['date_of_birth'])
                # convert JSON back to OIEPatientData for consistency (so it is either Patient or OIEPatientData)
                patient_json['mrns'] = [
                    OIEMRNData(**mrn)
                    for mrn in patient_json['mrns']
                ]
                patient_json['date_of_birth'] = date_of_birth
                patient = OIEPatientData(**patient_json)

            kwargs.update({
                'patient': patient,
            })

            if step == 'relationship':
                caregiver_pk: Optional[int] = storage.get('caregiver', None)  # type: ignore[assignment]

                if caregiver_pk:
                    caregiver = CaregiverProfile.objects.get(pk=caregiver_pk)

                    kwargs.update({'existing_user': caregiver})
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
            is_current_step = step == current_step
            # use the request data for the current step
            # otherwise, load the form data from session storage
            data = self.request.POST if is_current_step else self._get_saved_form_data(step)
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
            if is_current_step and 'X-Up-Validate' in self.request.headers:
                data = {}

            form = form_class(
                # pass none instead of empty dict to not bind the form
                data=data or None,
                initial=initial,
                **self._get_form_kwargs(step, is_current_step),
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

        data = self.request.POST
        # convert data from queryset to dict
        initial = data.dict()

        # use initial instead of data to avoid validating a form when up-validate is used
        form = self.form_class(
            data=None if 'X-Up-Validate' in self.request.headers else data,
            initial=initial,
            instance=relationship_record,
        )
        # when the post is triggered by up validate
        if 'X-Up-Validate' in self.request.headers:
            context_data = form.get_context()
        # when the post is triggered by submit/save button
        else:
            if form.is_valid():
                return super().post(request, **kwargs)
            else:
                context_data = form.get_context()

        context_data['relationship'] = relationship_record
        # keep original cancel_url
        context_data['cancel_url'] = request.POST.get('cancel_url')
        # update the form with context data when post does not succeed
        return self.render_to_response(context_data)

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
