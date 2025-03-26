"""This module provides views for patient settings."""
from typing import Any, List, Tuple

from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from coreapi import Object
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView

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


class RelationshipTypeDeleteView(generic.edit.DeleteView):
    """
    A view that displays a confirmation page and deletes an existing `RelationshipType` object.

    The given relationship type object will only be deleted if the request method is **POST**.

    If this view is fetched via **GET**, it will display a confirmation page with a form that POSTs to the same URL.
    """

    model = RelationshipType
    template_name = 'patients/relationship_type/confirm_delete.html'
    success_url = reverse_lazy('patients:relationshiptype-list')


class AccessRequestView(SessionWizardView):
    """
    This class inherits 'NamedUrlSessionWizardView', which each step has a url link to it.

    Using class 'NamedUrlSessionWizardView' preselects the backend used for storing information.
    """

    model = Site
    form_list = [('site', SelectSiteForm)]
    template_list = {'site': 'patients/access_request/access_request.html'}

    def get_template_names(self) -> List[str]:
        """
        Return the template url for a step.

        Returns:
            the template url for a step
        """
        return [self.template_list[self.steps.current]]

    def get_context_data(self, form: Any, **kwargs: Any) -> Object:
        """
        Return the template context for a step.

        Args:
            form: a list of different forms
            kwargs: additional keyword arguments

        Returns:
            the template context for a step
        """
        return super().get_context_data(form=form, **kwargs)

    def done(self, form_list: Tuple, **kwargs: Any) -> HttpResponseRedirect:
        """
        Redirect to a test qr code page.

        Args:
            form_list: a list of different forms
            kwargs: additional keyword arguments

        Returns:
            the object of HttpResponseRedirect
        """
        return HttpResponseRedirect(reverse_lazy('patients:generate-qr-code'))


class QrCode(generic.list.ListView):
    """Create qrcode using `qrcode` library not `django-qrcode`."""

    model = Site
    template_name = 'patients/access_request/test_qr_code.html'

    def get_context_data(self, **kwargs: Any) -> Object:
        """
        Redirect to a test qr code page.

        Args:
            kwargs: additional keyword arguments

        Returns:
            the object of HttpResponseRedirect
        """
        return {'qrcode': 'qr_image/testqr.svg'}
