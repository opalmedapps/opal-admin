"""Collection of managers for the caregiver app."""
import operator
from functools import reduce
from typing import TYPE_CHECKING, Any, Optional

from django.db import models
from django.db.models.functions import Coalesce

from . import constants
from . import models as patient_models

if TYPE_CHECKING:
    from opal.patients.models import Patient, Relationship, RelationshipType


class RelationshipManager(models.Manager['Relationship']):
    """Manager class for the `Relationship` model."""

    def get_patient_list_for_caregiver(self, user_name: str) -> models.QuerySet['Relationship']:
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
            'type',
        ).filter(
            caregiver__user__username=user_name,
        )

    def get_patient_id_list_for_caregiver(self, user_name: str) -> list[int]:
        """
        Get an array of patients' legacy IDs for a given caregiver.

        Args:
            user_name: User id making the request

        Returns:
            Return list of patients' legacy IDs
        """
        relationships = self.get_patient_list_for_caregiver(user_name=user_name)
        # filter out legacy_id=None to avoid typing problems when doing at the DB-level
        # the result type is otherwise ValuesQuerySet[Relationship, Optional[int]]
        return [
            legacy_id
            for legacy_id in relationships.values_list('patient__legacy_id', flat=True)
            if legacy_id is not None
        ]

    def get_relationship_by_patient_caregiver(
        self,
        relationship_type: str,
        user_id: int,
        ramq: Optional[str],
    ) -> models.QuerySet['Relationship']:
        """
        Query manager to get a `Relationship` record filtered by given parameters.

        Args:
            relationship_type (str): caregiver relationship type
            user_id (int): user id
            ramq (str): patient's RAMQ number

        Returns:
            Queryset to get the filtered `Relationship` record
        """
        return self.select_related(
            'patient',
            'type',
            'caregiver',
            'caregiver__user',
        ).filter(
            patient__ramq=ramq,
            type__name=relationship_type,
            caregiver__user__id=user_id,
        )


class RelationshipTypeManager(models.Manager['RelationshipType']):
    """Manager class for the `RelationshipType` model."""

    def filter_by_patient_age(self, patient_age: int) -> models.QuerySet['RelationshipType']:
        """Return a new QuerySet filtered by the patient age between start_age and end_age.

        Args:
            patient_age: patient's ages.

        Returns:
            a queryset of the relationship type.
        """
        return self.annotate(
            end_age_number=Coalesce('end_age', constants.RELATIONSHIP_MAX_AGE),
        ).filter(start_age__lte=patient_age, end_age_number__gt=patient_age)

    def self_type(self) -> 'RelationshipType':
        """
        Return the Self relationship type.

        Returns:
            the relationship type representing the self type
        """
        return self.get(role_type=patient_models.RoleType.SELF)

    def parent_guardian(self) -> 'RelationshipType':
        """
        Return the Parent/Guardian relationship type.

        Returns:
            the relationship type representing the parent/guardian type
        """
        return self.get(role_type=patient_models.RoleType.PARENT_GUARDIAN)

    def guardian_caregiver(self) -> 'RelationshipType':
        """
        Return the Guardian-Caregiver relationship type.

        Returns:
            the relationship type representing the guardian-caregiver type
        """
        return self.get(role_type=patient_models.RoleType.GUARDIAN_CAREGIVER)

    def mandatary(self) -> 'RelationshipType':
        """
        Return the Mandatary relationship type.

        Returns:
            the relationship type representing the mandatary type
        """
        return self.get(role_type=patient_models.RoleType.MANDATARY)


class PatientQueryset(models.QuerySet['Patient']):
    """Custom QuerySet class for the `Patient` model."""

    def get_patient_by_site_mrn_list(
        self,
        site_mrn_list: list[dict[str, Any]],
    ) -> 'Patient':
        """
        Query manager to get a `Patient` object filtered by a given list of dictionaries with sites and MRNs.

        Args:
            site_mrn_list: list of dictionaries containing sites and MRNs

        Returns:
            `Patient` object
        """
        # Create list of Q objects to filter by MRN/site pairs exclusively
        # E.g., [Q(mrn='9999996', site='RVH'), Q(mrn='9999997', site='MGH')]
        filters = [
            models.Q(
                hospital_patients__mrn=item.get('mrn'),
                hospital_patients__site__code=item['site']['code'],
            )
            for item in site_mrn_list
        ]

        # Use 'reduce' operation with 'operator.or_' to combine the Q objects
        # https://www.geeksforgeeks.org/reduce-in-python/
        # The resulting query: {... WHERE ((mrn=9999996 AND code=RVH) OR (mrn=99999997 AND code=MGH)) }
        query = reduce(operator.or_, filters)

        # Get `Patient` object filtered by MRNs AND sites
        return self.filter(query).distinct().get()


class PatientManager(models.Manager['Patient']):
    """Manager class for the `Patient` model."""
