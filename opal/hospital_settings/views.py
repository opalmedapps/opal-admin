"""This module provides views for hospital-specific settings."""
from typing import Any

from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView

from opal.core.views import CreateUpdateView

from .models import Institution, RelationshipType, Site


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


# see: https://stackoverflow.com/q/17192737
class CreateUpdateView(UpdateView):
    """Generic view that can handle creation and updating of objects."""

    def get_object(self, queryset: QuerySet = None) -> Any:
        """
        Return the object the view is displaying.

        Return `None` if an object is created instead.

        Args:
            queryset: the queryset to retrieve the object with or `None`

        Returns:
            the object or `None` if no object found (object is being created)
        """
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None


class RelationshipTypeListView(ListView):
    """This `ListView` provides a page that displays a list of `RelationshipType` objects."""

    model = RelationshipType
    ordering = ['pk']
    template_name = 'hospital_settings/relationship_type/list.html'


class RelationshipTypeCreateUpdateView(CreateUpdateView):
    """
    This `CreateView` displays a form for creating an `RelationshipType` object.

    It redisplays the form with validation errors (if there are any) and saves the `RelationshipType` object.
    """

    model = RelationshipType
    template_name = 'hospital_settings/relationship_type/form.html'
    fields = [
        'name_en',
        'name_fr',
        'description_en',
        'description_fr',
        'start_age',
        'end_age',
        'form_required',
    ]
    success_url = reverse_lazy('hospital-settings:relationshiptype-list')


class RelationshipTypeDeleteView(DeleteView):
    """
    A view that displays a confirmation page and deletes an existing `RelationshipType` object.

    The given relationship type object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = RelationshipType
    template_name = 'hospital_settings/relationship_type/confirm_delete.html'
    success_url = reverse_lazy('hospital-settings:relationshiptype-list')
