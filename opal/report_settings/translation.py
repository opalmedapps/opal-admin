"""This module provides translation options for the report settings models."""
from modeltranslation.translator import TranslationOptions, register

from .models import ReportTemplate


@register(ReportTemplate)
class ReportTemplateTranslationOptions(TranslationOptions):
    """This class provides translation options for [ReportTemplate][opal.report_settings.models.ReportTemplate]."""

    fields = ('name', 'logo', 'header')
    required_languages = ('en', 'fr')
