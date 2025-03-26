"""Management command for changing relationships' status to 'expired'."""
from typing import Any

from django.core.management.base import BaseCommand

from opal.patients.models import Relationship, RelationshipStatus


class Command(BaseCommand):
    """Command for setting relationships as expired once the patient reaches the relationship type's end age."""

    help = (  # noqa: A003
        'Checks all confirmed relationships, and sets as expired those for which the patient '
        + "has reached or exceeded the relationship's end age."
    )

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Iterate through all confirmed relationships to set as expired those with the patient's age >= end_age.

        Args:
            args: Input arguments.
            kwargs: Input keyword arguments.
        """
        number_of_updates = 0

        relationships_to_check = Relationship.objects.select_related(
            'patient',
            'type',
        ).filter(
            status=RelationshipStatus.CONFIRMED,
        ).exclude(type__end_age=None)

        for relationship in relationships_to_check:
            patient_age = relationship.patient.age

            if relationship.type.end_age and patient_age >= relationship.type.end_age:
                relationship.status = RelationshipStatus.EXPIRED
                relationship.save()
                number_of_updates += 1
                self.stdout.write(
                    'Expired relationship: id={id} | age {age} >= {end_age} end_age'.format(
                        id=relationship.id,
                        age=patient_age,
                        end_age=relationship.type.end_age,
                    ),
                )

        self.stdout.write(f'Updated {number_of_updates} relationship(s) from confirmed to expired.')
