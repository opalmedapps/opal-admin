# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for Users Caregivers migration."""

from typing import Any

from django.core.management.base import BaseCommand

from opal.caregivers.models import CaregiverProfile
from opal.legacy.models import LegacyPatient, LegacyUsers, LegacyUserType
from opal.patients.models import Patient, Relationship, RelationshipStatus, RelationshipType
from opal.users.models import Caregiver


class Command(BaseCommand):
    """Command to migrate Caregivers from legacy DB to Caregivers in New Backend."""

    help = 'migrate Caregivers from legacy DB to New backend DB'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate Caregivers from legacy DB to New backend DB.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        relationship_type = RelationshipType.objects.self_type()

        migrated_users_count = 0
        legacy_users = LegacyUsers.objects.filter(usertype=LegacyUserType.PATIENT)

        for legacy_user in legacy_users:
            patient = Patient.objects.filter(legacy_id=legacy_user.usertypesernum).first()
            if patient:
                caregiver_profile = CaregiverProfile.objects.filter(legacy_id=legacy_user.usersernum).first()
                if caregiver_profile:
                    self.stdout.write(
                        f'Nothing to be done for sernum: {legacy_user.usersernum}, skipping.',
                    )
                else:
                    legacy_patient = LegacyPatient.objects.get(patientsernum=legacy_user.usertypesernum)
                    caregiver_profile = self._create_caregiver_and_profile(legacy_patient, legacy_user)
                    # count number of migrated caregivers
                    migrated_users_count += 1

                self._create_relationship(patient, caregiver_profile, relationship_type)
            else:
                self.stderr.write(
                    self.style.WARNING(
                        f'Patient with sernum: {legacy_user.usertypesernum}, does not exist, skipping.',
                    )
                )
        self.stdout.write(
            f'Number of imported caregivers is: {migrated_users_count} (out of {legacy_users.count()})',
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
        phone_number = f'+1{legacy_patient.tel_num}' if legacy_patient.tel_num else ''
        caregiver_user = Caregiver(
            username=legacy_user.username,
            first_name=legacy_patient.first_name,
            last_name=legacy_patient.last_name,
            email=legacy_patient.email,
            date_joined=legacy_patient.registration_date,
            language=legacy_patient.language.lower(),
            phone_number=phone_number,
        )
        # User passwords aren't currently saved in Django
        caregiver_user.set_unusable_password()
        caregiver_user.full_clean()
        caregiver_user.save()

        caregiver_profile = CaregiverProfile(
            user=caregiver_user,
            legacy_id=legacy_user.usersernum,
        )
        caregiver_profile.full_clean()
        caregiver_profile.save()

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
                self.style.WARNING(
                    f'Self relationship for patient with legacy_id: {patient.legacy_id} already exists.',
                )
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
