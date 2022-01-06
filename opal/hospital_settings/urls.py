from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'institutions', views.InstitutionViewSet, basename='institution')
router.register(r'sites', views.SiteViewSet, basename='site')

urlpatterns = [
    path('', include(router.urls)),
]
