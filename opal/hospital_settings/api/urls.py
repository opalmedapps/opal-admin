"""
URL configuration for hospital-specific settings.

Provides URLs for the API and any additional paths for regular views.
"""
from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter

from . import views

# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
router = DefaultRouter()
router.register('institutions', views.InstitutionViewSet, basename='institution')
router.register('sites', views.SiteViewSet, basename='site')


urlpatterns = [
    path('hospital-settings/', include((router.urls, 'api-hospital-settings'))),
]
