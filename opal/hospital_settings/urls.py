"""
URL configuration for hospital-specific settings.

Provides URLs for the API and any additional paths for regular views.
"""
from django.urls import path

from . import views

app_name = 'hospital-settings'

urlpatterns = [
    # Web pages
    # Hospital settings index page
    path('', views.IndexTemplateView.as_view(), name='index'),
    # Institution pages
    path(
        'institutions/',
        views.InstitutionListView.as_view(),
        name='institution-list',
    ),
    path(
        'institution/<int:pk>/',
        views.InstitutionDetailView.as_view(),
        name='institution-detail',
    ),
    path(
        'institution/create/',
        views.InstitutionCreateUpdateView.as_view(),
        name='institution-create',
    ),
    path(
        'institution/<int:pk>/update/',
        views.InstitutionCreateUpdateView.as_view(),
        name='institution-update',
    ),
    path(
        'institution/<int:pk>/delete/',
        views.InstitutionDeleteView.as_view(),
        name='institution-delete',
    ),
    # Site pages
    path(
        'sites/',
        views.SiteListView.as_view(),
        name='site-list',
    ),
    path(
        'site/<int:pk>/',
        views.SiteDetailView.as_view(),
        name='site-detail',
    ),
    path(
        'site/create/',
        views.SiteCreateUpdateView.as_view(),
        name='site-create',
    ),
    path(
        'site/<int:pk>/update/',
        views.SiteCreateUpdateView.as_view(),
        name='site-update',
    ),
    path(
        'site/<int:pk>/delete/',
        views.SiteDeleteView.as_view(),
        name='site-delete',
    ),
]
