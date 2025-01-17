"""
Opal project URL configuration file.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/dev/topics/http/urls/

Examples:
    Function views
        1. Add an import:  from my_app import views
        2. Add a URL to urlpatterns:  path('', views.home, name='home')
    Class-based views
        1. Add an import:  from other_app.views import Home
        2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
    Including another URLconf
        1. Import the include() function: from django.urls import include, path
        2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.urls.conf import include
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from opal.core.views import LoginView

urlpatterns = [
    # REST API
    path('api/', include('opal.core.api_urls', namespace='api')),
    # DRF SPECTACULAR API URLS
    # JSON-based schema for external system requests
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger web-based API UI
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # apps
    path('health-data/', include('opal.health_data.urls')),
    path('hospital-settings/', include('opal.hospital_settings.urls')),
    path('patients/', include('opal.patients.urls')),
    path('questionnaires/', include('opal.questionnaires.urls')),
    path('usage-statistics/', include('opal.usage_statistics.urls')),
    # global config
    path(settings.ADMIN_URL, admin.site.urls),
    # define simple login view reusing the admin template
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    # define start URL as this might be expected by certain packages to exist
    # (e.g., DRF auth/login without a ?next parameter)
    path('', RedirectView.as_view(url='/hospital-settings/'), name='start'),
    # Make favicon available in admin site (causes ConnectionResetError otherwise)
    path(
        'favicon.ico',
        RedirectView.as_view(permanent=True, url=staticfiles_storage.url('images/favicon.ico')),
        name='favicon.ico',
    ),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

admin.site.site_header = _('Opal Management')
admin.site.site_title = _('Opal Backend Admin')
