"""
URL configuration for usage statistics.

Provides URLs for regular views.
"""

from django.urls import path

from . import views

app_name = 'usage-statistics'

urlpatterns = [
    # Usage statistics pages
    path(
        'reports/group/',
        views.GroupUsageStatisticsView.as_view(),
        name='reports-group-export',
    ),
    path(
        'reports/individual/',
        views.IndividualUsageStatisticsView.as_view(),
        name='reports-individual-export',
    ),
]
