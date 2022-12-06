"""This module provides views for hospital-specific settings."""
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.views.generic.edit import DeleteView

from django_tables2 import MultiTableMixin, SingleTableView

from opal.core.views import CreateUpdateView, UpdateView

from .forms import ManageCaregiverAccessForm, RelationshipPendingAccessForm
from .models import Relationship, RelationshipStatus, RelationshipType
from .tables import (
    PendingRelationshipTable,
    RelationshipCaregiverTable,
    RelationshipPatientTable,
    RelationshipTypeTable,
)


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
        'can_answer_questionnaire',
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


class PendingRelationshipListView(SingleTableView):
    """This view provides a page that displays a list of `RelationshipType` objects."""

    model = Relationship
    table_class = PendingRelationshipTable
    ordering = ['request_date']
    template_name = 'patients/relationships/pending/list.html'
    queryset = Relationship.objects.filter(status=RelationshipStatus.PENDING)


class PendingRelationshipUpdateView(UpdateView):
    """
    This `UpdatesView` displays a form for updating a `Relationship` object.

    It redisplays the form with validation errors (if there are any) and saves the `Relationship` object.
    """

    model = Relationship
    template_name = 'patients/relationships/pending/form.html'
    form_class = RelationshipPendingAccessForm
    success_url = reverse_lazy('patients:relationships-pending-list')


class CaregiverAccessView(MultiTableMixin, FormView):
    """This view provides a page that lists all caregivers for a specific patient."""

    tables = [
        RelationshipPatientTable,
        RelationshipCaregiverTable,
    ]
    # TODO: remove Relationship.objects.all(), currently it returns data for testing purposes
    # TODO: use Relationship.objects.none()
    tables_data = [
        Relationship.objects.all(),
        Relationship.objects.all(),
    ]
    template_name = 'patients/relationships-search/form.html'
    form_class = ManageCaregiverAccessForm
    success_url = reverse_lazy('patients:caregiver-access')
