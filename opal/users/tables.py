"""Table definitions for models of the caregivers app."""
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables

from opal.users.models import User


class UserTable(tables.Table):
    """
    A table for users.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
        extra_context={
            'urlname_update': 'users:user-update',
        },
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'language',
        ]
        empty_text = _('No users found.')
