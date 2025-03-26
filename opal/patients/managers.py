"""Collection of managers for the caregiver app."""

from django.db import models


class RelationshipManager(models.Manager):
    """Manager class for the `Relationship` model."""

    def get_patient_list_for_caregiver(self, user_id: str) -> models.QuerySet:
        """
        Query manager to get a list of patients for a given caregiver.

        Args:
            user_id: User id making the request

        Returns:
            Queryset to get the list of patients

        """
        return self.prefetch_related(
            'patient',
            'caregiver',
            'caregiver__user',
        ).filter(
            caregiver__user__username=user_id,
        )

    def get_patient_id_list_for_caregiver(self, user_id: str) -> list[int]:
        """
        Get a array of patients legacy IDs for a given caregiver.

        Args:
            user_id: User id making the request

        Returns:
            Return list of patient legacy IDs
        """
        relationships = self.get_patient_list_for_caregiver(user_id=user_id)
        return list(relationships.values_list('patient__legacy_id', flat=True))


class HospitalPatientManager(models.Manager):
    """Manager class for the `HospitalPatient` model."""

    def get_hospital_patient_by_site_mrn(
        self,
        site: str,
        mrn: str,
    ) -> models.QuerySet:
        """
        Query manager to get a `HospitalPatient` record filtered by given site code and MRN.

        Args:
            site (str): site code used to filter the records (e.g., MGH)
            mrn (str): medical record number (MRN) used to filter the records (e.g., 9999996)

        Returns:
            Queryset to get the filtered `HospitalPatient` record
        """
        return self.select_related(
            'site',
            'patient',
        ).filter(
            site__code=site,
            mrn=mrn,
        )
