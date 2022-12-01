"""This module provides views for hospital-specific settings."""
from django.urls import reverse_lazy
from django.views.generic.edit import DeleteView

from django_tables2 import SingleTableView

from opal.core.views import CreateUpdateView

from .forms import RelationshipPendingAccessForm
from .models import Relationship, RelationshipStatus, RelationshipType
from .tables import PendingRelationshipTable, RelationshipTypeTable


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


class PendingRelationshipCreateUpdateView(CreateUpdateView):
    """
    This `CreateView` displays a form for creating a `Relationship` object.

    It redisplays the form with validation errors (if there are any) and saves the `Relationship` object.
    """

    model = Relationship
    template_name = 'patients/relationships/pending/form.html'
    form_class = RelationshipPendingAccessForm
    success_url = reverse_lazy('patients:relationships-pending-list')
