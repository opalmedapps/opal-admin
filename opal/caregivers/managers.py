"""Collection of managers for the caregiver app."""
from django.db import models


class CaregiverManager(models.Manager):
    """Caregivers manager class."""

    def get_patient_list_for_caregiver(self, user_id: str) -> models.QuerySet:
        """
        Query manager to get a list of patient for a given caregiver.

        Args:
            user_id: User id making the requets

        Returns:
            Queryset to get the list of patient

        """
        return self.prefetch_related(
            'patient',
            'caregiver',
            'caregiver__user',
        ).filter(
            caregiver__user__username=user_id,
        )
