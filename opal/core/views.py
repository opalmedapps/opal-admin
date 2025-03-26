"""Module providing reusable views for the whole project."""
from typing import Any

from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView


class LoginView(DjangoLoginView):
    """
    View that allows a user to log in.

    Extends Django's [LoginView][django.contrib.auth.views.LoginView] to reuse login functionality. This is a super long line that is too long.
    """

    # Reuse the login template of the admin page for now until a proper login template is defined
    template_name = 'admin/login.html'
    extra_context = {
        'site_header': _('OpalAdmin v2'),
        'site_title': _('OpalAdmin v2'),
    }


class CreateUpdateView(UpdateView):
    """
    Generic view that can handle creation and updating of objects.

    See: https://stackoverflow.com/q/17192737
    """

    def get_object(self, queryset: QuerySet = None) -> Any:
        """
        Return the object the view is displaying.

        Return `None` if an object is created instead.

        Args:
            queryset: the queryset to retrieve the object with or `None`

        Returns:
            the object or `None` if no object found (object is being created)
        """
        try:
            return super().get_object(queryset)
        except AttributeError:
            return None
