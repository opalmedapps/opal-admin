"""Module providing models for the caregivers app."""
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from opal.users.models import User


class CaregiverProfile(models.Model):
    """Profile for caregiver users."""

    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        on_delete=models.PROTECT,
        limit_choices_to={'type': User.UserType.CAREGIVER},
    )
    legacy_id = models.PositiveIntegerField(
        verbose_name=_('Legacy ID'),
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Caregiver Profile')
        verbose_name_plural = _('Caregiver Profiles')

    def __str__(self) -> str:
        """
        Return the string representation of the associated user.

        Returns:
            the name of the associated user
        """
        return '{first} {last}'.format(first=self.user.first_name, last=self.user.last_name)


class SecurityQuestion(models.Model):
    """Security question model."""

    title = models.CharField(
        verbose_name=_('Title'),
        max_length=100,
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
    )

    class Meta:
        verbose_name = _('Security Question')
        verbose_name_plural = _('Security Questions')

    def __str__(self) -> str:
        """Return the question text.

        Returns:
            the question text.
        """
        return '{title}'.format(title=self.title)


class SecurityAnswer(models.Model):
    """Security answer model."""

    question = models.CharField(
        verbose_name=_('Question'),
        max_length=100,
    )

    user = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver Profile'),
        related_name='security_answers',
        on_delete=models.CASCADE,
    )

    answer = models.CharField(
        verbose_name=_('Answer'),
        max_length=128,
    )

    class Meta:
        verbose_name = _('Security Answer')
        verbose_name_plural = _('Security Answers')

    def __str__(self) -> str:
        """Return the caregiver and the question.

        Returns:
            the caregiver and the question.
        """
        return '{user} - {question} - {answer}'.format(
            user=self.user,
            question=self.question,
            answer=self.answer,
        )
