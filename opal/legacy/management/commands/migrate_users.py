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
        relationship_type = RelationshipType.objects.filter(role_type=RoleType.SELF).first()

        # force failure if the relationship type does not exist
        if relationship_type is None:
            raise CommandError("RelationshipType for 'Self' not found")

        migrated_users_count = 0

        for legacy_user in LegacyUsers.objects.filter(usertype='Patient'):
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
                    caregiver_profile = self._create_caregiver_and_profile(legacy_patient, legacy_user)
                    # count number of migrated users
                    migrated_users_count += 1

                self._create_relationship(patient, caregiver_profile, relationship_type)
            else:
                self.stderr.write(
                    'Patient with sernum: {legacy_id}, does not exist, skipping.'.format(
                        legacy_id=legacy_user.usertypesernum,
                    ),
                )
        self.stdout.write(
            f'Number of imported users is: {migrated_users_count}',
        )

    def _create_caregiver_and_profile(
        self,
        legacy_patient: LegacyPatient,
        legacy_user: LegacyUsers,
    ) -> CaregiverProfile:
        """
        Create `Caregiver` and corresponding `CaregiverProfile` instances for the given legacy patient and user.

        Returns the created `CaregiverProfile` instance.

        Args:
            legacy_patient: the legacy patient
            legacy_user: the legacy user corresponding to the patient

        Returns:
            CaregiverProfile: the created `CaregiverProfile` instance
        """
        # convert phone number in int to str
        phone_number = '+1{0}'.format(legacy_patient.telnum) if legacy_patient.telnum else ''
        caregiver_user = Caregiver(
            username=legacy_user.username,
            first_name=legacy_patient.firstname,
            last_name=legacy_patient.lastname,
            email=legacy_patient.email,
            date_joined=legacy_patient.registrationdate,
            language=legacy_patient.language.lower(),
            phone_number=phone_number,
        )
        caregiver_user.full_clean(exclude=['password'])
        caregiver_user.save()

        caregiver_profile = CaregiverProfile(
            user=caregiver_user,
            legacy_id=legacy_user.usersernum,
        )
        caregiver_profile.full_clean()
        caregiver_profile.save()

        self.stdout.write(
            'Legacy user with sernum: {legacy_id} has been migrated'.format(
                legacy_id=legacy_user.usersernum,
            ),
        )

        return caregiver_profile

    def _create_relationship(
        self,
        patient: Patient,
        caregiver_profile: CaregiverProfile,
        relationship_type: RelationshipType,
    ) -> None:
        """
            Check the self relationship between caregiver and patient and migrated if it does not exist.

        Args:
            patient: instance of Patient model.
            caregiver_profile: instance of CaregiverProfile model.
            relationship_type: the `RelationshipType` instance for Self.

        """
        relationship = Relationship.objects.filter(
            patient=patient,
            caregiver=caregiver_profile,
            type=relationship_type,
        ).first()
        if relationship:
            self.stdout.write(
                'Self relationship for patient with legacy_id: {legacy_id} already exists.'.format(
                    legacy_id=patient.legacy_id,
                ),
            )
        else:
            relationship = Relationship(
                patient=patient,
                caregiver=caregiver_profile,
                type=relationship_type,
                status=RelationshipStatus.CONFIRMED,
                request_date=caregiver_profile.user.date_joined,
                start_date=caregiver_profile.user.date_joined,
                reason='',
            )
            relationship.full_clean()
            relationship.save()

            self.stdout.write(
                'Self relationship for patient with legacy_id: {legacy_id} has been created.'.format(
                    legacy_id=patient.legacy_id,
                ),
            )
