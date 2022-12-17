"""Command for detecting deviations in the questionnaire respondent/caregiver between MariaDB and Django databases."""
from typing import Any

from django.core.management.base import BaseCommand

SPLIT_LENGTH = 120


class Command(BaseCommand):
    """Command to find differences in the questionnaire respondent data between legacy and new back end databases.

    The command compares the `respondentUsername` field of the `QuestionnaireDB.answerQuestionnaire` table with the \
    `first_name` and the `last_name` of the same `CaregiverProfile` stored in the Django back end.
    """

    help = '{0} {1}'.format(  # noqa: A003
        'Check the `first_name` and `last_name` of the questionnaire respondents are in sync',
        'with those stored for the same caregiver in Django.',
    )
    requires_migrations_checks = True

    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Handle sync check for the questionnaire respondents.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
