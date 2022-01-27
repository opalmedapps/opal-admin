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
    # REST APIs
    path('api/hospital-settings/', include((router.urls, 'api-hospital-settings'))),

    # Web pages
    path('', views.HomePageView.as_view(), name='index'),
    path(
        'hospital-settings/institutions/',
        views.InstitutionListView.as_view(),
        name='institution-list'
    ),
    path(
        'hospital-settings/institution/<int:pk>/',
        views.InstitutionDetailView.as_view(),
        name='institution-detail'
    ),
    path(
        'hospital-settings/institution/create/',
        views.InstitutionCreateView.as_view(),
        name='institution-create'
    ),
    path(
        'hospital-settings/institution/<int:pk>/update/',
        views.InstitutionUpdateView.as_view(),
        name='institution-update'
    ),
    path(
        'hospital-settings/institution/<int:pk>/delete/',
        views.InstitutionDeleteView.as_view(),
        name='institution-delete'
    ),
    path(
        'hospital-settings/sites/',
        views.SiteListView.as_view(),
        name='site-list'
    ),
    path(
        'hospital-settings/site/<int:pk>/',
        views.SiteDetailView.as_view(),
        name='site-detail'
    ),
    path(
        'hospital-settings/site/create/',
        views.SiteCreateView.as_view(),
        name='site-create'
    ),
    path(
        'hospital-settings/site/<int:pk>/update/',
        views.SiteUpdateView.as_view(),
        name='site-update'
    ),
    path(
        'hospital-settings/site/<int:pk>/delete/',
        views.SiteDeleteView.as_view(),
        name='site-delete'
    ),
]
