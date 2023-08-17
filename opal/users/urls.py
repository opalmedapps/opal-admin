"""
URL configuration for patients.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    # Caregiver pages
    path(
        'caregivers/',
        views.CaregiverListView.as_view(),
        name='caregivers-list',
    ),
    path(
        'caregivers/<int:pk>/',
        views.UpdateCaregiverView.as_view(),
        name='user-update',
    ),
]
