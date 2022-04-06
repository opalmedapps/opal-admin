"""Module providing views for the whole project."""
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.utils.translation import gettext_lazy as _


class LoginView(DjangoLoginView):
    """
    View that allows a user to log in.

    Extends Django's [LoginView][django.contrib.auth.views.LoginView] to reuse login functionality.
    """

    # Reuse the login template of the admin page for now until a proper login template is defined
    template_name = 'admin/login.html'
    extra_context = {
        'site_header': _('OpalAdmin v2'),
        'site_title': _('OpalAdmin v2'),
    }
