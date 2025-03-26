"""Command for Security Question migration."""
from typing import Any

from django.core.management.base import BaseCommand

from opal.caregivers.models import SecurityQuestion
from opal.legacy.models import LegacySecurityQuestion


class Command(BaseCommand):
    """Command to migrate Security Question from legacy DB to backend DB."""

    help = 'migrate Security Question from legacy DB to backend DB'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate Security Question from legacy DB to backend DB.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
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
                    'Security question import succeeded, sernum: {questionsernum}'.format(
                        questionsernum=legacy_question.securityquestionsernum,
                    ),
                )
