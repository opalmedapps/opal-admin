"""Command for Security Answer migration."""
from typing import Any, Dict

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand

from opal.caregivers.models import CaregiverProfile, SecurityAnswer, SecurityQuestion
from opal.legacy.models import LegacySecurityanswer, LegacySecurityquestion, LegacyUsers
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
        legacy_answers = LegacySecurityanswer.objects.all()
        for legacy_answer in legacy_answers:

            legacy_patient = legacy_answer.patientsernum
            user = self._check_users(legacy_patient.patientsernum)
            user = user['user']
            if user is None:
                continue

            legacy_question = legacy_answer.securityquestionsernum
            question = self._check_and_import_question(legacy_question.securityquestionsernum)
            question = question['question']
            if question is None:
                continue

            # Import caregiver according to the user
            try:
                caregiver = CaregiverProfile.objects.get(user_id=user.id)
            except ObjectDoesNotExist:
                caregiver = CaregiverProfile.objects.create(user=user)

            # Import SecurityAnwser
            try:
                SecurityAnswer.objects.get(user_id=caregiver.id)
            except ObjectDoesNotExist:
                SecurityAnswer.objects.create(
                    user=caregiver,
                    question=question.title,
                    answer=legacy_answer.answertext,
                )

    def _check_and_import_question(self, securityquestionsernum: int) -> Dict:
        """
        Check legacy security question and security question exist or not.

        Args:
            securityquestionsernum: legacy security question patientsernum.

        Returns:
            Return SecurityQuestion or return None.
        """
        # Skip anwer import if related legacy question not found
        try:
            legacy_question = LegacySecurityquestion.objects.get(
                securityquestionsernum=securityquestionsernum,
            )
        except ObjectDoesNotExist:
            return {'question': None}

        # Import SecurityQuestion according to legacy security question
        try:
            question = SecurityQuestion.objects.get(title_en=legacy_question.questiontext_en)
        except ObjectDoesNotExist:
            question = SecurityQuestion.objects.create(
                title_en=legacy_question.questiontext_en,
                title_fr=legacy_question.questiontext_fr,
            )
        return {'question': question}

    def _check_users(self, patientsernum: int) -> Dict:
        """
        Check legacy user and user exist or not according the legacy patientsernum.

        Args:
            patientsernum: legacy patient patientsernum.

        Returns:
            Return user if found otherwise return None.
        """
        # Skip anwer import if related legacy user not found
        try:
            legacy_user = LegacyUsers.objects.get(usertypesernum=patientsernum)
        except ObjectDoesNotExist:
            return {'user': None}
        except MultipleObjectsReturned:
            return {'user': None}

        # Skip anwer import if related user not found
        try:
            user = User.objects.get(username=legacy_user.username)
        except ObjectDoesNotExist:
            # TODO not sure how to import user
            return {'user': None}
        return {'user': user}
