"""
URL configuration for the project-wide REST API.

Inspired by Two Scoops of Django Section 17.3.
"""
from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter

from opal.hospital_settings.api import viewsets as settings_views

# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
router = DefaultRouter()
router.register('institutions', settings_views.InstitutionViewSet, basename='institution')
router.register('sites', settings_views.SiteViewSet, basename='site')

app_name = 'core'

urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('', include(router.urls)),
]
