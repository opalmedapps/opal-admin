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
        'group-reports/',
        views.GroupUsageStatisticsView.as_view(),
        name='group-reports-export',
    ),
    path(
        'individual-reports/',
        views.IndividualUsageStatisticsView.as_view(),
        name='individual-reports-export',
    ),
]
