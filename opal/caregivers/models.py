"""Module providing models for the caregivers app."""
from django.conf import settings
from django.contrib.auth import hashers
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
        verbose_name=_('Is Active'),
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

    HASH_SALT = 'MUHC_MCGILL'

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

    def set_hash_answer(self, raw_answer: str) -> None:
        """Set answer text.

        Args:
            raw_answer: raw_answer the origianl answer text
        """
        if not bool(getattr(settings, 'QUESTIONS_CASE_SENSITIVE', False)):
            raw_answer = raw_answer.upper()
        # we need to use salt, so that the hash result is not random
        self.answer = hashers.make_password(raw_answer, self.HASH_SALT)

    def update_answer(self, raw_answer: str) -> None:
        """Update answer text.

        Args:
            raw_answer: raw_answer the origianl answer text
        """
        self.set_hash_answer(raw_answer)
        self.save(update_fields=['answer'])

    def check_answer(self, raw_answer: str) -> bool:
        """Check and save answer text. (api function).

        Args:
            raw_answer: raw_answer the origianl answer text

        Returns:
            the result of hasers check_password
        """
        if not bool(getattr(settings, 'QUESTIONS_CASE_SENSITIVE', False)):
            raw_answer = raw_answer.upper()

        return hashers.check_password(raw_answer, self.answer, self.update_answer)

    def set_unusable_answer(self) -> str:
        """Set unusable answer."""
        self.answer = hashers.make_password(None)

    def has_usable_answer(self) -> bool:
        """Return the result of the answer is usable or not.

        Returns:
            the result of the answer is usable or not
        """
        return hashers.is_password_usable(self.answer)
