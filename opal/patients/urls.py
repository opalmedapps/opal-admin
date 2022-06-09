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
        views.IndexView.as_view(),
        name='index',
    ),
    # Search patient page
    path(
        'search-patient/',
        views.SearchPatientView.as_view(),
        name='search-patient',
    ),
    # Patient result page
    path(
        'fetch-patient/',
        views.FetchPatientView.as_view(),
        name='fetch-patient',
    ),
    # Requestor details page
    path(
        'requestor-details/',
        views.RequestorDetailsView.as_view(),
        name='requestor-details',
    ),
    # Verify requestor's identification page
    path(
        'verify-identification/',
        views.VerifyIdentificationView.as_view(),
        name='verify-identification',
    ),
    # Generate QR code page
    path(
        'generate-qr/',
        views.GenerateQRView.as_view(),
        name='generate-qr',
    ),
]
