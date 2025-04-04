# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for Security Answer migration."""

from typing import Any

from django.core.management.base import BaseCommand

from opal.caregivers.models import CaregiverProfile, SecurityAnswer
from opal.legacy.models import LegacySecurityAnswer, LegacyUsers, LegacyUserType
from opal.users.models import User


class Command(BaseCommand):
    """Command to migrate Security Answer from legacy DB to backend DB."""

    help = 'migrate Security Answer from legacy DB to backend DB'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate Security Answer from legacy DB to backend DB.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        migrated_answers = 0
        legacy_answers = LegacySecurityAnswer.objects.all()

        for legacy_answer in legacy_answers:
            legacy_patient = legacy_answer.patient
            user = self._find_user(legacy_patient.patientsernum)
            if user is None:
                self.stderr.write(
                    self.style.ERROR(
                        'Security answer import failed, sernum: {answersernum}, details: {details}'.format(
                            answersernum=legacy_answer.securityanswersernum,
                            details='User does not exist',
                        ),
                    )
                )
                continue

            # Check caregiver according to the user, skip import if not found.
            try:
                caregiver = CaregiverProfile.objects.get(user_id=user.id)
            except CaregiverProfile.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        'Security answer import failed, sernum: {answersernum}, details: {details}'.format(
                            answersernum=legacy_answer.securityanswersernum,
                            details='Caregiver does not exist',
                        ),
                    )
                )
                continue

            legacy_question = legacy_answer.securityquestionsernum
            question = legacy_question.questiontext_fr if user.language == 'fr' else legacy_question.questiontext_en

            try:
                SecurityAnswer.objects.get(
                    user_id=caregiver.id,
                    question=question,
                    answer=legacy_answer.answertext,
                )
            except SecurityAnswer.DoesNotExist:
                SecurityAnswer.objects.create(
                    user=caregiver,
                    question=question,
                    answer=legacy_answer.answertext,
                )
                migrated_answers += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Security answer already exists, sernum: {legacy_answer.securityanswersernum}',
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Migrated {migrated_answers} out of {legacy_answers.count()} security answers',
            )
        )

    def _find_user(self, patientsernum: int) -> User | None:
        """
        Check legacy user and user exist or not according the legacy patientsernum.

        Args:
            patientsernum: legacy patient patientsernum.

        Returns:
            Return user if found otherwise return None.
        """
        # Skip answer import if related legacy user not found
        legacy_user = None
        user = None
        try:
            legacy_user = LegacyUsers.objects.get(usertypesernum=patientsernum, usertype=LegacyUserType.PATIENT)
        except LegacyUsers.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    f'Legacy user does not exist, usertypesernum: {patientsernum}',
                )
            )
        except LegacyUsers.MultipleObjectsReturned:
            self.stderr.write(
                self.style.ERROR(
                    f'Found more than one related legacy users, usertypesernum: {patientsernum}',
                )
            )

        if legacy_user:
            # Skip answer import if related user not found
            try:
                user = User.objects.get(username=legacy_user.username)
            except User.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(
                        f'User does not exist, username: {legacy_user.username}',
                    )
                )
        return user
