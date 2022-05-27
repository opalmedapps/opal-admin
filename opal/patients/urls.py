"""
URL configuration for Patients.

Provides URLs for the API and any additional paths for regular views.
"""
from django.urls import path

from . import views

app_name = 'patients'

urlpatterns = [
    # Web pages
    # Patient index page
    path(
        '',
        views.IndexTemplateView.as_view(),
        name='index',
    ),
]
