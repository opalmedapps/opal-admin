"""
URL configuration for patients.

Provides URLs for regular views.
"""
from django.urls import path

from . import views

app_name = 'patients'

urlpatterns = [
    path(
        '<str:code>/register/',
        views.RegistrationRegisterView.as_view(),
        name='registration-register',
    ),
]
