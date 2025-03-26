"""This module provides views for patient settings."""
import io
from typing import Any, List, Tuple

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

import qrcode
from coreapi import Object
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView
from qrcode.image import svg

from opal.core.views import CreateUpdateView
from opal.patients.forms import SearchForm, SelectSiteForm

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
    Form wizard view providing the steps for a caregiver's patient access request.

    The collected information is stored in the server-side session. Once all information is collected,
    a confirmation page with a QR code is displayed.
    """

    model = Site
    form_list = [
        ('site', SelectSiteForm),
        ('search', SearchForm),
    ]
    template_list = {
        'site': 'patients/access_request/access_request.html',
        'search': 'patients/access_request/access_request.html',
    }

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
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current == 'site':
            context.update({'header_title': _('Hospital Information')})
        elif self.steps.current == 'search':
            context.update({'header_title': _('Patient Details')})
            site_selection = self.get_cleaned_data_for_step(self.steps.prev)
            self.request.session['site_selection'] = str(site_selection['sites'])

        return context

    def get_form_initial(self, step: str) -> Any:
        """
        Return a dictionary which will be passed to the form for `step` as `initial`.

        If no initial data was provided while initializing the form wizard, an empty dictionary will be returned.

        Args:
            step: a form step

        Returns:
            a dictionary or an empty dictionary for a step
        """
        initial = self.initial_dict.get(step, {})
        if step == 'site' and 'site_selection' in self.request.session:
            initial.update({
                'sites': Site.objects.get(name=self.request.session['site_selection']),
            })
        return initial

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
        factory = svg.SvgImage
        img = qrcode.make(form_data[0]['sites'], image_factory=factory, box_size=10)
        stream = io.BytesIO()
        img.save(stream)

        return render(self.request, 'patients/access_request/test_qr_code.html', {
            'svg': stream.getvalue().decode(),
        })
