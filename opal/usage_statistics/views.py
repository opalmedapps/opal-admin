"""This module provides views for the usage statistics application."""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import Form
from django.views import generic

from opal.usage_statistics import forms

# EXPORT USAGE STATISTICS PAGES


class SuperUserPermissionsFormViewMixin(UserPassesTestMixin, generic.FormView[Form]):
    """`FormView` mixin that ensures the request is coming from a user with a `superuser` permissions."""

    def test_func(self) -> bool:
        """Check if the request is coming from `superuser`.

        The request is rejected for non-superusers.

        Returns:
            bool: `True` if the request is sent by superuser. `False` otherwise.
        """
        return self.request.user.is_superuser


class GroupUsageStatisticsView(SuperUserPermissionsFormViewMixin):
    """View that displays a form for exporting usage statistics."""

    form_class = forms.GroupUsageStatisticsForm
    template_name = 'usage_statistics/export_data/export_form.html'


class IndividualUsageStatisticsView(SuperUserPermissionsFormViewMixin):
    """View that displays a form for exporting usage statistics."""

    form_class = forms.IndividualUsageStatisticsForm
    template_name = 'usage_statistics/export_data/export_form.html'
