"""Module providing models for the caregivers app."""
from django.core.exceptions import ValidationError
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

    question_en = models.CharField(
        verbose_name=_('Question Text EN'),
        max_length=2056,
    )

    question_fr = models.CharField(
        verbose_name=_('Question Text FR'),
        max_length=2056,
    )

    created_at = models.DateField(
        verbose_name=_('Creation Date'),
    )

    updated_at = models.DateField(
        verbose_name=_('Last Updated'),
    )

    is_active = models.BooleanField(
        verbose_name=_('Active'),
        default=True,
    )

    class Meta:
        verbose_name = _('Security Question')
        verbose_name_plural = _('Security Questions')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',  # noqa: WPS323
                check=models.Q(created_at__lte=models.F('updated_at')),
            ),
        ]

    def __str__(self) -> str:
        """Return the question text EN as default.

        Returns:
            the question text EN as default.
        """
        return '{en} {fr}'.format(en=self.question_en, fr=self.question_fr)

    def clean(self) -> None:
        """Validate if last updated date is earlier creation date.

        Raises:
            ValidationError: the error shows when updated_at is earlier than created_at
        """
        if self.created_at is not None and self.created_at > self.updated_at:
            raise ValidationError({'created_at': _('Creation date should be earlier than last updated date.')})


class SecurityAnswer(models.Model):
    """Security answer model."""

    question = models.ForeignKey(
        to=SecurityQuestion,
        verbose_name=_('Security Question'),
        related_name='security_answers',
        on_delete=models.CASCADE,
    )

    profile = models.ForeignKey(
        to=CaregiverProfile,
        verbose_name=_('Caregiver Profile'),
        related_name='security_answers',
        on_delete=models.CASCADE,
    )

    answer = models.CharField(
        verbose_name=_('Security Answer'),
        max_length=2056,
    )

    created_at = models.DateField(
        verbose_name=_('Creation Date'),
    )

    updated_at = models.DateField(
        verbose_name=_('Last Updated'),
    )

    class Meta:
        verbose_name = _('Security Answer')
        verbose_name_plural = _('Security Answers')

        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_date_valid',  # noqa: WPS323
                check=models.Q(created_at__lte=models.F('updated_at')),
            ),
        ]

    def __str__(self) -> str:
        """Return the caregiver and the question.

        Returns:
            the caregiver and the question.
        """
        return '{profile} - {question}'.format(profile=self.profile, question=self.question)

    def clean(self) -> None:
        """Validate if last updated date is earlier creation date.

        Raises:
            ValidationError: the error shows when updated_at is earlier than created_at
        """
        if self.created_at is not None and self.created_at > self.updated_at:
            raise ValidationError({'created_at': _('Creation date should be earlier than last updated date.')})
