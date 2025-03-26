"""Table definitions for models of the questionnaires app."""
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables


class ReportTable(tables.Table):
    """A table for viewing questionnaire reports."""

    patientId = tables.Column(verbose_name=_('Patient ID'), orderable=False)
    questionId = tables.Column(verbose_name=_('Question ID'), orderable=False)
    question = tables.Column(verbose_name=_('Question Text'), orderable=False)
    Answer = tables.Column(verbose_name=_('Answer Text'), orderable=False)
    creationDate = tables.DateColumn(verbose_name=_('Date Created'), orderable=False)
    lastUpdated = tables.DateColumn(verbose_name=_('Date Updated'), orderable=False)

    class Meta:
        empty_text = _('No responses found.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }
