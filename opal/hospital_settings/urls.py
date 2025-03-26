"""
URL configuration for hospital-specific settings.

Provides URLs for the API and any additional paths for regular views.
"""
from django.urls import path
from django.urls.conf import include
from django.views.generic.base import RedirectView

from . import views

app_name = 'hospital-settings'

urlpatterns = [
    # REST API
    path('api/', include('opal.hospital_settings.api.urls')),
    path('', RedirectView.as_view(url='/hospital-settings/'), name='start'),
    # Web pages
    # Hospital settings index page
    path('hospital-settings/', views.IndexTemplateView.as_view(), name='index'),
    # Institution pages
    path(
        'hospital-settings/institutions/',
        views.InstitutionListView.as_view(),
        name='institution-list',
    ),
    path(
        'hospital-settings/institution/<int:pk>/',
        views.InstitutionDetailView.as_view(),
        name='institution-detail',
    ),
    path(
        'hospital-settings/institution/create/',
        views.InstitutionCreateView.as_view(),
        name='institution-create',
    ),
    path(
        'hospital-settings/institution/<int:pk>/update/',
        views.InstitutionUpdateView.as_view(),
        name='institution-update',
    ),
    path(
        'hospital-settings/institution/<int:pk>/delete/',
        views.InstitutionDeleteView.as_view(),
        name='institution-delete',
    ),
    # Site pages
    path(
        'hospital-settings/sites/',
        views.SiteListView.as_view(),
        name='site-list',
    ),
    path(
        'hospital-settings/site/<int:pk>/',
        views.SiteDetailView.as_view(),
        name='site-detail',
    ),
    path(
        'hospital-settings/site/create/',
        views.SiteCreateView.as_view(),
        name='site-create',
    ),
    path(
        'hospital-settings/site/<int:pk>/update/',
        views.SiteUpdateView.as_view(),
        name='site-update',
    ),
    path(
        'hospital-settings/site/<int:pk>/delete/',
        views.SiteDeleteView.as_view(),
        name='site-delete',
    ),
]
