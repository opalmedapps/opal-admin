"""Module providing admin functionality for the caregivers app."""
from django.contrib import admin

from .models import CaregiverProfile

admin.site.register(CaregiverProfile, admin.ModelAdmin)
