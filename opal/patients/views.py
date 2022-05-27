"""This module provides views for Patients."""
from django.views.generic.list import ListView

from opal.hospital_settings.models import Site


# PATIENTS INDEX PAGE
class IndexTemplateView(ListView):
    """This `TemplateView` provides an index page for the Patients app."""

    model = Site
    template_name = 'patients/index.html'
