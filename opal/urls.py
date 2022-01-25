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
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import path
from django.urls.conf import include
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView

urlpatterns = [
    # REST API authentification
    path('api/auth/', include('dj_rest_auth.urls')),

    # global config
    path('admin/', admin.site.urls),
    # hospital settings app
    path('', include('opal.hospital_settings.urls')),
    # path('', RedirectView.as_view(url='/api/hospital-settings/'), name='start'),
    # Make favicon available in admin site (causes ConnectionResetError otherwise)
    path(
        'favicon.ico',
        RedirectView.as_view(permanent=True, url=staticfiles_storage.url('images/favicon.ico')),
        name='favicon.ico',
    ),
]

admin.site.site_header = _('Opal Management')
admin.site.site_title = _('Opal Backend Admin')
