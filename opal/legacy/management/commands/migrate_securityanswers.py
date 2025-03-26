"""Command for Security Answer migration."""
from typing import Any

from django.core.management.base import BaseCommand

from opal.caregivers.models import CaregiverProfile, SecurityAnswer, SecurityQuestion
from opal.legacy.models import LegacySecurityAnswer, LegacySecurityQuestion, LegacyUsers
from opal.users.models import User


class Command(BaseCommand):
    """Command to migrate Security Answer from legacy DB to backend DB."""

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
            user = self._check_users(legacy_patient.patientsernum)
            if user is None:
                continue

            legacy_question = legacy_answer.securityquestionsernum
            question = self._check_and_import_question(legacy_question.securityquestionsernum)
            if question is None:
                continue

            # Check caregiver according to the user, skip import if not found.
            try:
                caregiver = CaregiverProfile.objects.get(user_id=user.id)
            except CaregiverProfile.DoesNotExist:
                continue

            # Import SecurityAnwser or create if it does not exist.
            try:
                SecurityAnswer.objects.get(
                    user_id=caregiver.id,
                    question=question.title,
                    answer=legacy_answer.answertext,
                )
            except SecurityAnswer.DoesNotExist:
                SecurityAnswer.objects.create(
                    user=caregiver,
                    question=question.title,
                    answer=legacy_answer.answertext,
                )

    def _check_and_import_question(self, securityquestionsernum: int) -> Any:
        """
        Check legacy security question exists or not.

        Args:
            securityquestionsernum: legacy security question sernum.

        Returns:
            Return SecurityQuestion or None.
        """
        # Skip answer import if related legacy question not found
        try:
            legacy_question = LegacySecurityQuestion.objects.get(
                securityquestionsernum=securityquestionsernum,
            )
        except LegacySecurityQuestion.DoesNotExist:
            return None

        # Import SecurityQuestion according to legacy security question or create if not exists.
        try:
            question = SecurityQuestion.objects.get(title_en=legacy_question.questiontext_en)
        except SecurityQuestion.DoesNotExist:
            return None
        return question

    def _check_users(self, patientsernum: int) -> Any:
        """
        Check legacy user and user exist or not according the legacy patientsernum.

        Args:
            patientsernum: legacy patient patientsernum.

        Returns:
            Return user if found otherwise return None.
        """
        # Skip answer import if related legacy user not found
        try:
            legacy_user = LegacyUsers.objects.get(usertypesernum=patientsernum)
        except LegacyUsers.DoesNotExist:
            return None
        except LegacyUsers.MultipleObjectsReturned:
            return None

        # Skip anwer import if related user not found
        try:
            user = User.objects.get(username=legacy_user.username)
        except User.DoesNotExist:
            # TODO not sure how to import user
            return None
        return user
