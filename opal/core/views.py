"""Module providing reusable views for the whole project."""
from typing import Any, Generic, Optional, TypeVar

from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db.models import Model, QuerySet
from django.forms.models import ModelForm
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

_Model = TypeVar('_Model', bound=Model)


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


class CreateUpdateView(Generic[_Model], UpdateView[_Model, ModelForm[_Model]]):
    """
    Generic view that can handle creation and updating of objects.

    See: https://stackoverflow.com/q/17192737
    """

    # TODO: change signature to be consistent with superclass (-> _Model)
    def get_object(self, queryset: Optional[QuerySet[_Model]] = None) -> Any:
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
