"""Command for Security Answer migration."""
from typing import Any, Optional

from django.core.management.base import BaseCommand

from opal.caregivers.models import CaregiverProfile, SecurityAnswer
from opal.legacy.models import LegacySecurityAnswer, LegacyUsers
from opal.users.models import User


class Command(BaseCommand):
    """Command to migrate Security Answer from legacy DB to backend DB."""

    help = 'migrate Security Answer from legacy DB to backend DB'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: C901 WPS231 WPS210
        """
        Handle migrate Security Answer from legacy DB to backend DB.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        legacy_answers = LegacySecurityAnswer.objects.all()
        for legacy_answer in legacy_answers:

            legacy_patient = legacy_answer.patientsernum
            user = self._find_user(legacy_patient.patientsernum)
            if user is None:
                self.stderr.write(
                    'Security answer import failed, sernum: {answersernum}, details: {details}'.format(
                        answersernum=legacy_answer.securityanswersernum,
                        details='User does not exist',
                    ),
                )
                continue

            # Check caregiver according to the user, skip import if not found.
            try:
                caregiver = CaregiverProfile.objects.get(user_id=user.id)
            except CaregiverProfile.DoesNotExist:
                self.stderr.write(
                    'Security answer import failed, sernum: {answersernum}, details: {details}'.format(
                        answersernum=legacy_answer.securityanswersernum,
                        details='Caregiver does not exist',
                    ),
                )
                continue

            legacy_question = legacy_answer.securityquestionsernum
            question_text = legacy_question.questiontext_en  # English
            if user.language == 'fr':  # French
                question_text = legacy_question.questiontext_fr

            # Import SecurityAnwser or create if it does not exist.
            try:
                SecurityAnswer.objects.get(
                    user_id=caregiver.id,
                    question=question_text,
                    answer=legacy_answer.answertext,
                )
            except SecurityAnswer.DoesNotExist:
                SecurityAnswer.objects.create(
                    user=caregiver,
                    question=question_text,
                    answer=legacy_answer.answertext,
                )
                self.stdout.write(
                    'Security answer import succeeded, sernum: {answersernum}'.format(
                        answersernum=legacy_answer.securityanswersernum,
                    ),
                )
                continue
            self.stdout.write(
                'Security answer already exists, sernum: {answersernum}'.format(
                    answersernum=legacy_answer.securityanswersernum,
                ),
            )

    def _find_user(self, patientsernum: int) -> Optional[User]:  # noqa: C901
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
            legacy_user = LegacyUsers.objects.get(usertypesernum=patientsernum, usertype='Patient')
        except LegacyUsers.DoesNotExist:
            self.stderr.write(
                'Legacy user does not exist, usertypesernum: {usertypesernum}'.format(
                    usertypesernum=patientsernum,
                ),
            )
        except LegacyUsers.MultipleObjectsReturned:
            self.stderr.write(
                'Found more than one related legacy users, usertypesernum: {usertypesernum}'.format(
                    usertypesernum=patientsernum,
                ),
            )

        if legacy_user:
            # Skip anwer import if related user not found
            try:
                user = User.objects.get(username=legacy_user.username)
            except User.DoesNotExist:
                self.stderr.write(
                    'User does not exist, username: {username}'.format(
                        username=legacy_user.username,
                    ),
                )
        return user
