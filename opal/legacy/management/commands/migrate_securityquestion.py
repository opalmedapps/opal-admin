"""Command for Security Question migration."""
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from opal.caregivers.models import SecurityQuestion
from opal.legacy.models import LegacySecurityquestion


class Command(BaseCommand):
    """Command to migrate Security Question from legacy DB to backend DB."""

    def handle(self, *args, **kwargs) -> None:
        """
        Handle migrate Security Question from legacy DB to backend DB.

        Return 'None'.

        Args:
            args: input arguments.
            kwargs: input arguments.
        """
        legacy_questions = LegacySecurityquestion.objects.all()
        for legacy_question in legacy_questions:
            try:
                SecurityQuestion.objects.get(title_en=legacy_question.questiontext_en)
            except ObjectDoesNotExist:
                SecurityQuestion.objects.create(
                    title_en=legacy_question.questiontext_en,
                    title_fr=legacy_question.questiontext_fr,
                )
