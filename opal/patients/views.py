"""This module provides views for hospital-specific settings."""
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView

from django_tables2 import SingleTableView
from formtools.wizard.views import NamedUrlSessionWizardView

from opal.core.views import CreateUpdateView
from opal.patients.forms import SelectSiteForm

from .models import RelationshipType, Site
from .tables import RelationshipTypeTable


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


class RelationshipTypeDeleteView(DeleteView):
    """
    A view that displays a confirmation page and deletes an existing `RelationshipType` object.

    The given relationship type object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = RelationshipType
    template_name = 'patients/relationship_type/confirm_delete.html'
    success_url = reverse_lazy('patients:relationshiptype-list')


class UrlWizardViews(NamedUrlSessionWizardView):
    """
    This class inherits named url session wizard, which each step has a url link to it.

    Using named url is good for api-framework to link it to a specific step
    """

    model = Site
    form_list = [('site', SelectSiteForm)]

    def get_template_names(self) -> str:
        """
        Return a template url.

        Returns:
            the url of the template
        """
        return 'patients/wizard_forms/wizard_forms.html'
