"""Collection of managers for the caregiver app."""

from django.db import models


class RelationshipManager(models.Manager):
    """Manager class for the `Relationship` model."""

    def get_patient_list_for_caregiver(self, user_name: str) -> models.QuerySet:
        """
        Query manager to get a list of patients for a given caregiver.

        Args:
            user_name: User id making the request

        Returns:
            Queryset to get the list of patients

        """
        return self.prefetch_related(
            'patient',
            'caregiver',
            'caregiver__user',
        ).filter(
            caregiver__user__username=user_name,
        )

    def get_patient_id_list_for_caregiver(self, user_name: str) -> list[int]:
        """
        Get a array of patients legacy IDs for a given caregiver.

        Args:
            user_name: User id making the request

        Returns:
            Return list of patient legacy IDs
        """
        relationships = self.get_patient_list_for_caregiver(user_name=user_name)
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
            site: site code used to filter the records (e.g., MGH)
            mrn: medical record number (MRN) used to filter the records (e.g., 9999996)

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

    def get_hospital_patient_by_site_mrn_list(
        self,
        site_mrn_list: list[dict],
    ) -> models.QuerySet:
        """
        Query manager to get a `HospitalPatient` record filtered by given list of dictionaries with site codes and MRNs.

        Args:
            site_mrn_list: list of dictionaries that contain site codes and MRNs

        Returns:
            Queryset to get the filtered `HospitalPatient` record
        """
        # Create flat lists of MRNs and site codes
        mrns = [hospital_patient.get('mrn') for hospital_patient in site_mrn_list]
        sites = [hospital_patient['site']['code'] for hospital_patient in site_mrn_list]

        # Get `HospitalPatient` queryset filtered by MRNs AND site codes
        hospital_patients = self.filter(
            models.Q(mrn__in=mrns) & models.Q(site__code__in=sites),
        )

        # Get first `HospitalPatient` object from the queryset
        hospital_patient = hospital_patients.first()

        # Return `None` if the `Patient` objects in the queryset are not the same (refer to different patients)
        if (
            not hospital_patient
            or len(hospital_patients) != hospital_patients.filter(patient_id=hospital_patient.patient_id).count()
        ):
            return self.none()

        return hospital_patients
