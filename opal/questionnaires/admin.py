"""This module provides admin options for questionnaire models."""
from django.contrib import admin

from . import models

admin.site.register(models.QuestionnaireProfile, admin.ModelAdmin)
