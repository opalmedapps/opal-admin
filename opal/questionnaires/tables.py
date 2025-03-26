"""Table definitions for models of the questionnaires app."""
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables


class ReportTable(tables.Table):
    """A table for viewing questionnaire reports."""

    patientId = tables.Column(orderable=False)
    questionId = tables.Column(orderable=False)
    question = tables.Column(orderable=False)
    Answer = tables.Column(orderable=False)
    creationDate = tables.Column(orderable=False)
    lastUpdated = tables.Column(orderable=False)

    class Meta:
        empty_text = _('No responses found.')
        attrs = {
            'class': 'table table-bordered table-hover',
            'thead': {
                'class': 'thead-light',
            },
        }
