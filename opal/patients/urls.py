"""
URL configuration for patients.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'patients'

urlpatterns = [
    # Manage Caregiver Access Pages
    path(
        'relationships/pending/',
        views.PendingRelationshipListView.as_view(),
        name='relationships-pending-list',
    ),
    path(
        'relationships/pending/<int:pk>/update/',
        views.ManagePendingUpdateView.as_view(),
        name='relationships-pending-update',
    ),
    path(
        'relationships/pending/<int:pk>/readonly/',
        views.ManagePendingReadOnlyView.as_view(),
        name='relationships-pending-readonly',
    ),
    # Relationship Types Pages
    path(
        'relationship-types/',
        views.RelationshipTypeListView.as_view(),
        name='relationshiptype-list',
    ),
    path(
        'relationship-type/create/',
        views.RelationshipTypeCreateUpdateView.as_view(),
        name='relationshiptype-create',
    ),
    path(
        'relationship-type/<int:pk>/update/',
        views.RelationshipTypeCreateUpdateView.as_view(),
        name='relationshiptype-update',
    ),
    path(
        'relationship-type/<int:pk>/delete/',
        views.RelationshipTypeDeleteView.as_view(),
        name='relationshiptype-delete',
    ),
    # Access request pages
    path(
        'access-request/',
        views.AccessRequestView.as_view(views.AccessRequestView.form_list),
        name='access-request',
    ),
]
