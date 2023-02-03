"""Command for setting relationships to expired when the patient reaches the right age."""
from typing import Any

from django.core.management.base import BaseCommand

from opal.patients.models import Patient, Relationship, RelationshipStatus


class Command(BaseCommand):
    """TODO"""

    help = 'TODO'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """TODO"""
        number_of_updates = 0

        relationships_to_check = Relationship.objects.select_related(
            'patient',
            'type',
        ).filter(
            status=RelationshipStatus.CONFIRMED,
            type__end_age__isnull=False,
        )

        for relationship in relationships_to_check:
            patient_age = Patient.calculate_age(date_of_birth=relationship.patient.date_of_birth)
            self.stdout.write(
                f'Evaluating relationship: id={relationship.id}'
                f' | age {patient_age} >= {relationship.type.end_age} end_age'
            )
            if patient_age >= relationship.type.end_age:
                relationship.status = RelationshipStatus.EXPIRED
                relationship.save()
                number_of_updates += 1
                self.stdout.write(
                    f'Expired relationship: id={relationship.id}'
                    f' | age {patient_age} >= {relationship.type.end_age} end_age'
                )

        self.stdout.write(
            f'Updated {number_of_updates} relationship(s) from confirmed to expired.'
        )
