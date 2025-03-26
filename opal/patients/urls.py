"""
URL configuration for patients.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'patients'

urlpatterns = [
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
]
