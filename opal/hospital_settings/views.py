"""This module provides views for hospital-specific settings."""
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms.models import ModelForm
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView

from django_tables2 import SingleTableView

from opal.core.views import CreateUpdateView

from . import tables
from .forms import InstitutionForm
from .models import Institution, Site


# HOSPITAL SETTINGS INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the hospital settings app."""

    template_name = 'hospital_settings/index.html'


# INSTITUTIONS
class InstitutionListView(PermissionRequiredMixin, SingleTableView):
    """This table view provides a page that displays a list of institution objects."""

    model = Institution
    permission_required = ('hospital_settings.can_manage_institutions',)
    table_class = tables.InstitutionTable
    template_name = 'hospital_settings/institution/institution_list.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Update the context with whether a new institution can be created.

        Args:
            kwargs: the context data

        Returns:
            the context dictionary
        """
        context = super().get_context_data(**kwargs)

        context['can_create'] = context['object_list'].count() == 0

        # django-tables2 overrides the definition of get_context_data
        # which loses the type hints from django-stubs
        # issue report: https://github.com/jieter/django-tables2/issues/894
        return context  # type: ignore[no-any-return]


class InstitutionCreateUpdateView(PermissionRequiredMixin, CreateUpdateView[Institution]):
    """
    This `CreateUpdateView` displays a form for creating and updating an institution object.

    It redisplays the form with validation errors (if there are any) and saves the institution object.
    """

    model = Institution
    permission_required = ('hospital_settings.can_manage_institutions',)
    template_name = 'hospital_settings/institution/institution_form.html'
    form_class = InstitutionForm
    success_url = reverse_lazy('hospital-settings:institution-list')


class InstitutionDeleteView(PermissionRequiredMixin, DeleteView[Institution, ModelForm[Institution]]):
    """
    A view that displays a confirmation page and deletes an existing institution object.

    The given institution object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    # see: https://github.com/typeddjango/django-stubs/issues/1227#issuecomment-1311472749
    object: Institution  # noqa: A003
    model = Institution
    permission_required = ('hospital_settings.can_manage_institutions',)
    template_name = 'hospital_settings/institution/institution_confirm_delete.html'
    success_url = reverse_lazy('hospital-settings:institution-list')


# SITES
class SiteListView(PermissionRequiredMixin, SingleTableView):
    """This table view provides a page that displays a list of site objects."""

    model = Site
    permission_required = ('hospital_settings.can_manage_sites',)
    table_class = tables.SiteTable
    template_name = 'hospital_settings/site/site_list.html'


class SiteCreateUpdateView(PermissionRequiredMixin, CreateUpdateView[Site]):
    """
    This `CreateView` displays a form for creating and updating a site object.

    It redisplays the form with validation errors (if there are any) and saves the site object.
    """

    model = Site
    permission_required = ('hospital_settings.can_manage_sites',)
    template_name = 'hospital_settings/site/site_form.html'
    fields = [
        'name_en',
        'name_fr',
        'parking_url_en',
        'parking_url_fr',
        'direction_url_en',
        'direction_url_fr',
        'code',
        'institution',
        'longitude',
        'latitude',
        'street_name',
        'street_number',
        'postal_code',
        'city',
        'province_code',
        'contact_telephone',
        'contact_fax',
    ]
    success_url = reverse_lazy('hospital-settings:site-list')


class SiteDeleteView(PermissionRequiredMixin, DeleteView[Site, ModelForm[Site]]):
    """
    A view that displays a confirmation page and deletes an existing site object.

    The given site object will only be deleted if the request method is **POST**.

    If the view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    # see: https://github.com/typeddjango/django-stubs/issues/1227#issuecomment-1311472749
    object: Site  # noqa: A003
    model = Site
    permission_required = ('hospital_settings.can_manage_sites',)
    template_name = 'hospital_settings/site/site_confirm_delete.html'
    success_url = reverse_lazy('hospital-settings:site-list')
