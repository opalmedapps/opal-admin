# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for detecting deviations in the questionnaire respondent/caregiver between MariaDB and Django databases."""
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from django.utils import timezone

SPLIT_LENGTH = 120

# consider only completed (status=2) and in progress (status=1) questionnaires
LEGACY_RESPONDENT_QUERY = """
    SELECT
        aq.respondentUsername AS Username,
        aq.respondentDisplayName AS CaregiverName
    FROM answerQuestionnaire aq
    WHERE aq.status = 1 OR aq.status = 2
    GROUP BY aq.respondentUsername, aq.respondentDisplayName;
"""

DJANGO_RESPONDENT_QUERY = """
    SELECT
        UU.username AS Username,
        CONCAT_WS(' ', UU.first_name, UU.last_name) AS CaregiverName
    FROM users_user UU
    WHERE UU.username IN %s;
"""


class Command(BaseCommand):
    """
    Command to find differences in the questionnaire respondent data between legacy and new back end databases.

    The command compares the `respondentUsername` field of the `QuestionnaireDB.answerQuestionnaire` table with the \
    `first_name` and the `last_name` of the same `CaregiverProfile` stored in the Django back end.
    """

    help = (
        'Check the `first_name` and `last_name` of the questionnaire respondents are in sync'
        + 'with those stored for the same caregiver in Django.'
    )
    requires_migrations_checks = True

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle sync check for the questionnaire respondents.

        Args:
            args: input arguments
            kwargs: input arguments

        Raises:
            CommandError: if there are deviations
        """
        with connections['questionnaire'].cursor() as questionnaire_db:
            questionnaire_db.execute(LEGACY_RESPONDENT_QUERY)
            legacy_respondents = questionnaire_db.fetchall()

        with connections['default'].cursor() as django_db:
            users = [respondent[0] for respondent in legacy_respondents]
            # users list is empty, set it with impossible while so the SQL query does not break
            if not users:
                users = ['___impossible_username___']
            django_db.execute(DJANGO_RESPONDENT_QUERY, [users])
            django_respondents = django_db.fetchall()

        respondents_err_str = self._get_respondents_sync_err(
            legacy_respondents,
            django_respondents,
        )

        if respondents_err_str:
            raise CommandError(respondents_err_str)

        self.stdout.write('No sync errors have been found in the in the questionnaire respondent data.')

    def _get_respondents_sync_err(
        self,
        legacy_respondents: list[tuple[str, ...]],
        django_respondents: list[tuple[str, ...]],
    ) -> str | None:
        """
        Build error string based on the questionnaire respondents' first & last names deviations.

        Args:
            legacy_respondents: Django's `Users'` first and last names filtered by `username`
            django_respondents: Legacy's `answerQuestionnaire.respondentUsername` respondents' names

        Returns:
            str: error with the `Patient` tables/models deviations if there are any, empty string otherwise
        """
        # Please see the details about the `symmetric_difference` method in the links below:
        # https://www.geeksforgeeks.org/python-set-symmetric_difference-2/
        # https://www.w3schools.com/python/ref_set_symmetric_difference.asp
        legacy_respondents_set = set(legacy_respondents)
        unmatched_respondents = legacy_respondents_set.symmetric_difference(django_respondents)

        # return `None` if there are no unmatched respondents
        if not unmatched_respondents:
            return None

        divider = SPLIT_LENGTH * '-'
        unmatched_respondents_string = '\n'.join(str(respondent) for respondent in (unmatched_respondents))
        return (
            f'\n{divider}'
            + f'\n{timezone.now()}: found deviations in the questionnaire respondents!!!\n\n'
            + '[QuestionnaireDB.answerQuestionnaire.respondentUsername  <===>  opal.users_user.first_name::last_name]\n'
            + '[format: (Username, CaregiverName)]:\n\n'
            # Add a list of unmatched questionnaire respondents' names to the error string
            + unmatched_respondents_string
            + f'\n{divider}\n\n\n'
        )
