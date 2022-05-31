"""This module provides views for hospital-specific settings."""
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView

from opal.core.views import CreateUpdateView

from .models import Institution, Site


# HOSPITAL SETTINGS INDEX PAGE
class IndexTemplateView(TemplateView):
    """This `TemplateView` provides an index page for the hospital settings app."""

    template_name = 'hospital_settings/index.html'


# INSTITUTIONS
class InstitutionListView(ListView):
    """This `ListView` provides a page that displays a list of institution objects."""

    model = Institution
    template_name = 'hospital_settings/institution/institution_list.html'


class InstitutionCreateUpdateView(CreateUpdateView):
    """
    This `CreateUpdateView` displays a form for creating and updating an institution object.

    It redisplays the form with validation errors (if there are any) and saves the institution object.
    """

    model = Institution
    template_name = 'hospital_settings/institution/institution_form.html'
    fields = ['name_en', 'name_fr', 'code']
    success_url = reverse_lazy('hospital-settings:institution-list')


class InstitutionDetailView(DetailView):
    """This `DetailView` provides a page that displays a single institution object."""

    model = Institution
    template_name = 'hospital_settings/institution/institution_detail.html'


class InstitutionDeleteView(DeleteView):
    """
    A view that displays a confirmation page and deletes an existing institution object.

    The given institution object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = Institution
    template_name = 'hospital_settings/institution/institution_confirm_delete.html'
    success_url = reverse_lazy('hospital-settings:institution-list')


# SITES
class SiteListView(ListView):
    """This `ListView` provides a page that displays a list of site objects."""

    model = Site
    template_name = 'hospital_settings/site/site_list.html'


class SiteCreateUpdateView(CreateUpdateView):
    """
    This `CreateView` displays a form for creating and updating a site object.

    It redisplays the form with validation errors (if there are any) and saves the site object.
    """

    model = Site
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
    ]
    success_url = reverse_lazy('hospital-settings:site-list')


class SiteDetailView(DetailView):
    """This `DetailView` provides a page that displays a single site object."""

    model = Site
    template_name = 'hospital_settings/site/site_detail.html'


class SiteDeleteView(DeleteView):
    """
    A view that displays a confirmation page and deletes an existing site object.

    The given site object will only be deleted if the request method is **POST**.

    If the view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = Site
    template_name = 'hospital_settings/site/site_confirm_delete.html'
    success_url = reverse_lazy('hospital-settings:site-list')
