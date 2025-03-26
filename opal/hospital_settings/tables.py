"""Table definitions for models of the hospital settings app."""
from types import MappingProxyType

from django.utils.translation import gettext_lazy as _

import django_tables2 as tables

from .models import Institution, Site

TABLE_ATTRS = MappingProxyType({
    'class': 'table table-bordered table-hover',
    'thead': {
        'class': 'thead-light',
    },
})


class InstitutionTable(tables.Table):
    """
    A table for institutions.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
        extra_context={
            'urlname_update': 'hospital-settings:institution-update',
            'urlname_delete': 'hospital-settings:institution-delete',
        },
    )

    class Meta:
        model = Institution
        fields = ['code', 'name', 'actions']
        empty_text = _('No institutions defined.')
        attrs = TABLE_ATTRS


class SiteTable(tables.Table):
    """
    A table for sites.

    Defines an additional action column for action buttons.
    """

    actions = tables.TemplateColumn(
        verbose_name=_('Actions'),
        template_name='tables/action_column.html',
        orderable=False,
        extra_context={
            'urlname_update': 'hospital-settings:site-update',
            'urlname_delete': 'hospital-settings:site-delete',
        },
    )

    class Meta:
        model = Site
        fields = ['code', 'name', 'actions']
        empty_text = _('No sites defined.')
        attrs = TABLE_ATTRS
