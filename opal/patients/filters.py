"""This module provides filters for `patients` app."""
import django_filters

from .models import Relationship


class ManageCaregiverAccessFilter(django_filters.FilterSet):
    """This `ManageCaregiverAccessFilter` declares filters for the `ManageCaregiverAccessForm` fields."""

    # sites =

    # medical_number =

    first_name = django_filters.CharFilter(field_name='patient__first_name', lookup_expr='iexact')

    class Meta:
        model = Relationship
        fields = ['first_name']
