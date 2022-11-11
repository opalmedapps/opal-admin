"""Collection of managers for the caregiver app."""

from django.db import models
from django.db.models.functions import Coalesce

from . import constants


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

    def get_relationship_by_patient_caregiver(  # noqa: WPS211
        self,
        relationship_type: str,
        first_name: str,
        last_name: str,
        user_id: int,
        ramq: str,
    ) -> models.QuerySet:
        """
        Query manager to get a `Relationship` record filtered by given parameters.

        Args:
            relationship_type (str): caregiver relationship type
            first_name (str): user first name
            last_name (str): user last name
            user_id (int): user id
            ramq (str): patient's RAMQ numebr

        Returns:
            Queryset to get the filtered `Relationship` record
        """
        return self.select_related(
            'patient',
            'type',
            'caregiver',
            'caregiver__user',
        ).filter(
            patient__first_name=first_name,
            patient__last_name=last_name,
            patient__ramq=ramq,
            type__name=relationship_type,
            caregiver__user__id=user_id,
        )


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


class RelationshipTypeManager(models.Manager):
    """Manager class for the `RelationshipType` model."""

    def filter_by_patient_age(self, patient_age: int) -> models.QuerySet:
        """Return a new QuerySet filtered by the patient age between start_age and end_age.

        Args:
            patient_age: patient's ages.

        Returns:
            a queryset of the relationship type.
        """
        return self.annotate(  # type: ignore[no-any-return]
            end_age_number=Coalesce('end_age', constants.RELATIONSHIP_MAX_AGE),
        ).filter(start_age__lte=patient_age, end_age_number__gt=patient_age)
