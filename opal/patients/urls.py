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
        'relationships/',
        views.ManageCaregiverAccessListView.as_view(),
        name='relationships-list',
    ),
    path(
        'relationships/<int:pk>/',
        views.ManageCaregiverAccessUpdateView.as_view(),
        name='relationships-view-update',
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
        views.AccessRequestView.as_view(),
        name='access-request',
    ),
    path(
        'access-request/confirmation/',
        views.AccessRequestConfirmationView.as_view(),
        name='access-request-confirmation',
    ),
    # Patient Setting pages
    path(
        'settings/search/',
        views.PatientSettingsListView.as_view(),
        name='patient_settings_list',
    ),
]
