"""Module providing model factories for Legacy database models."""

from django.utils import timezone

from factory import SubFactory
from factory.django import DjangoModelFactory

from . import models


class LegacyUserFactory(DjangoModelFactory):
    """Model factory for Legacy user."""

    class Meta:
        model = models.LegacyUsers

    usertypesernum = 51
    username = 'username'
    usertype = 'Patient'


class LegacyPatientFactory(DjangoModelFactory):
    """Model factory for Legacy Patient."""

    class Meta:
        model = models.LegacyPatient

    patientsernum = 51


class LegacyNotificationFactory(DjangoModelFactory):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyNotification

    readstatus = 0
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyAliasFactory(DjangoModelFactory):
    """Alias factory from the legacy database."""

    class Meta:
        model = models.LegacyAlias

    aliassernum = 283


class LegacyAliasexpressionFactory(DjangoModelFactory):
    """Legacy expression from legacy database."""

    class Meta:
        model = models.LegacyAliasexpression

    aliasexpressionsernum = 7399
    aliassernum = SubFactory(LegacyAliasFactory)


class LegacyAppointmentFactory(DjangoModelFactory):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyAppointment

    scheduledstarttime = timezone.now()
    checkin = 1
    status = 'Open'
    state = 'active'
    aliasexpressionsernum = SubFactory(LegacyAliasexpressionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
