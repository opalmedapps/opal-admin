"""Table definitions for models of the questionnaires app."""
from django.utils.translation import gettext_lazy as _

import django_tables2 as tables


class ReportTable(tables.Table):
    """A table for viewing questionnaire reports."""

    patient_id = tables.Column(verbose_name=_('Patient ID'), orderable=False)
    question_id = tables.Column(verbose_name=_('Question ID'), orderable=False)
    question = tables.Column(verbose_name=_('Question Text'), orderable=False)
    answer = tables.Column(verbose_name=_('Answer Text'), orderable=False)
    creation_date = tables.DateColumn(verbose_name=_('Date Created'), orderable=False)
    last_updated = tables.DateColumn(verbose_name=_('Date Updated'), orderable=False)

    class Meta:
        empty_text = _('No responses found.')
