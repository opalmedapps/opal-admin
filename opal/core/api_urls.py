"""
URL configuration for the project-wide REST API.

Inspired by Two Scoops of Django Section 17.3.
"""
from django.conf import settings
from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter, SimpleRouter

from opal.hospital_settings.api import viewsets as settings_views
from opal.legacy.api import views as legacy_views

# show APIRootView only in debug mode
# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
if settings.DEBUG:
    router: SimpleRouter = DefaultRouter()
else:
    router = SimpleRouter()

router.register('institutions', settings_views.InstitutionViewSet, basename='institutions')
router.register('sites', settings_views.SiteViewSet, basename='sites')

app_name = 'core'

urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('app/home/', legacy_views.AppHomeView.as_view(), name='app-home'),
    path(
        'patients/legacy/<int:legacy_id>/check_permissions/',
        legacy_views.CaregiverPermissionsView.as_view(),
        name='caregiver-permissions',
    ),
    path('', include(router.urls)),
]
