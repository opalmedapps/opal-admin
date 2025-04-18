# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
