from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter

from . import views

# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
router = DefaultRouter()
router.register(r'institutions', views.InstitutionViewSet, basename='institution')
router.register(r'sites', views.SiteViewSet, basename='site')

urlpatterns = [
    path('', include(router.urls)),
]
