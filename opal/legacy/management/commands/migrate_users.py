"""Command for Users Caregivers migration."""
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatient, LegacyUsers
from opal.patients.models import Patient, Relationship, RelationshipStatus, RelationshipType, RoleType
from opal.users.models import Caregiver


class Command(BaseCommand):
    """Command to migrate Users from legacy DB to Caregivers in New Backend."""

    help = 'migrate Users from legacy DB to New backend DB'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Handle migrate Users from legacy DB to New backend DB.

        Raises:
            CommandError: if the self RelationshipType does not exist

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        legacy_users = LegacyUsers.objects.filter(usertype='Patient')
        relationshiptype = RelationshipType.objects.filter(role_type=RoleType.SELF).first()

        # force failure if the relationship type does not exist
        if relationshiptype is None:
            raise CommandError("RelationshipType for 'Self' not found")

        migrated_users_count = 0
        for legacy_user in legacy_users:
            patient = Patient.objects.filter(legacy_id=legacy_user.usertypesernum).first()
            if patient:
                caregiver_profile = CaregiverProfile.objects.filter(legacy_id=legacy_user.usersernum).first()
                if caregiver_profile:
                    self.stdout.write(
                        'Nothing to be done for sernum: {legacy_id}, skipping.'.format(
                            legacy_id=legacy_user.usersernum,
                        ),
                    )
                else:
                    legacy_patient = LegacyPatient.objects.get(patientsernum=legacy_user.usertypesernum)
                    caregiver_user = Caregiver.objects.create(
                        username=legacy_user.username,
                        first_name=legacy_patient.firstname,
                        last_name=legacy_patient.lastname,
                        email=legacy_patient.email,
                        date_joined=legacy_patient.registrationdate,
                        language=legacy_patient.language.lower(),
                        phone_number=legacy_patient.telnum,
                    )
                    caregiver_profile = CaregiverProfile.objects.create(
                        user=caregiver_user,
                        legacy_id=legacy_user.usersernum,
                    )
                    self.stdout.write(
                        'Legacy user with sernum: {legacy_id} has been migrated'.format(
                            legacy_id=legacy_user.usersernum,
                        ),
                    )
                    # count number of migrated users
                    migrated_users_count += 1

                self._create_relationship(patient, caregiver_profile, relationshiptype)
            else:
                self.stderr.write(
                    'Patient with sernum: {legacy_id}, does not exist, skipping.'.format(
                        legacy_id=legacy_user.usertypesernum,
                    ),
                )
        self.stdout.write(
            f'Number of imported users is: {migrated_users_count}',
        )

    def _create_relationship(
        self,
        patient: Patient,
        caregiver_profile: CaregiverProfile,
        relationshiptype: RelationshipType,
    ) -> None:
        """
            Check the self relationship between caregiver and patient and migrated if it does not exist.

        Args:
            patient: instance of Patinet model.
            caregiver_profile: instance of CaregiverProfile model.
            relationshiptype: instance of RelationshipType model.

        """
        relationship = Relationship.objects.filter(
            patient=patient,
            caregiver=caregiver_profile,
            type=relationshiptype,
        ).first()
        if relationship:
            self.stdout.write(
                'Self relationship for patient with legacy_id: {legacy_id} already exists.'.format(
                    legacy_id=patient.legacy_id,
                ),
            )
        else:
            Relationship.objects.create(
                patient=patient,
                caregiver=caregiver_profile,
                type=relationshiptype,
                status=RelationshipStatus.CONFIRMED,
                request_date=caregiver_profile.user.date_joined,
                start_date=caregiver_profile.user.date_joined,
                reason='',
            )
            self.stdout.write(
                'Self relationship for patient with legacy_id: {legacy_id} has been created.'.format(
                    legacy_id=patient.legacy_id,
                ),
            )
