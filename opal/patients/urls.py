"""
URL configuration for patients.

Provides URLs for regular views.
"""
from django.urls import path, re_path

from . import views

app_name = 'patients'

form_wizard = views.UrlWizardViews.as_view(
    views.UrlWizardViews.form_list,
    url_name='patients:form_step',
    done_step_name='finished',
)

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
    # Patients pages
    re_path(
        '^form/(?P<step>.+)/$',
        form_wizard,
        name='form_step',
    ),
    path(
        'form/',
        form_wizard,
        name='form',
    ),
]
