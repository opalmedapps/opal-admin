# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for Security Question migration."""

from typing import Any

from django.core.management.base import BaseCommand

from opal.caregivers.models import SecurityQuestion
from opal.legacy.models import LegacySecurityQuestion


class Command(BaseCommand):
    """Command to migrate Security Question from legacy DB to the new backend."""

    help = 'migrate Security Question from legacy DB to the new backend'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate Security Question from legacy DB to the new backend.

        Return 'None'.

        Args:
            args: non-keyward input arguments.
            kwargs:  variable keyword input arguments.
        """
        legacy_questions = LegacySecurityQuestion.objects.all()
        for legacy_question in legacy_questions:
            # Import a security question if not found.
            try:
                SecurityQuestion.objects.get(title_en=legacy_question.questiontext_en)
            except SecurityQuestion.DoesNotExist:
                SecurityQuestion.objects.create(
                    title_en=legacy_question.questiontext_en,
                    title_fr=legacy_question.questiontext_fr,
                    is_active=bool(legacy_question.active),
                )
                self.stdout.write(
                    f'Imported security question, sernum: {legacy_question.securityquestionsernum}, title: {legacy_question.questiontext_en}',
                )
                continue
            self.stdout.write(
                f'Security question sernum: {legacy_question.securityquestionsernum}, title: {legacy_question.questiontext_en} exists already, skipping',
            )
