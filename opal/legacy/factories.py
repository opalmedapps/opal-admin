"""Module providing model factories for Legacy database models."""
from datetime import datetime

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
        django_get_or_create = ('patientsernum',)

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
    readstatus = 0
    aliasexpressionsernum = SubFactory(LegacyAliasexpressionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyDocumentFactory(DjangoModelFactory):
    """Document factory from the legacy database."""

    class Meta:
        model = models.LegacyDocument

    patientsernum = SubFactory(LegacyPatientFactory)
    readstatus = 0


class LegacyTxTeamMessageFactory(DjangoModelFactory):
    """Txteammessage factory from the legacy database."""

    class Meta:
        model = models.LegacyTxTeamMessage

    patientsernum = SubFactory(LegacyPatientFactory)
    readstatus = 0


class LegacyEducationalMaterialFactory(DjangoModelFactory):
    """Educational material factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterial

    patientsernum = SubFactory(LegacyPatientFactory)
    readstatus = 0


class LegacyQuestionnaireFactory(DjangoModelFactory):
    """Questionnaire factory from the legacy database."""

    class Meta:
        model = models.LegacyQuestionnaire

    patientsernum = SubFactory(LegacyPatientFactory)
    completedflag = 0


class LegacyAnnouncementFactory(DjangoModelFactory):
    """Announcement factory from the legacy database."""

    class Meta:
        model = models.LegacyAnnouncement

    patientsernum = SubFactory(LegacyPatientFactory)
    readstatus = 0


class LegacySecurityQuestionFactory(DjangoModelFactory):
    """SecurityQuestion factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityQuestion

    securityquestionsernum = 1
    questiontext_en = 'What is the name of your first pet?'
    questiontext_fr = 'Quel est le nom de votre premier animal de compagnie?'
    creationdate = datetime.strptime(
        '2022-09-27 11:11:11',
        '%Y-%m-%d %H:%M:%S',
    )
    lastupdated = datetime.strptime(
        '2022-09-27 11:11:11',
        '%Y-%m-%d %H:%M:%S',
    )
    active = 1


class LegacySecurityAnswerFactory(DjangoModelFactory):
    """SecurityAnswer factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityAnswer

    securityanswersernum = 1
    securityquestionsernum = SubFactory(LegacySecurityQuestionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
    answertext = 'bird'
    creationdate = datetime.strptime(
        '2022-09-27 11:11:11',
        '%Y-%m-%d %H:%M:%S',
    )
    lastupdated = datetime.strptime(
        '2022-09-27 11:11:11',
        '%Y-%m-%d %H:%M:%S',
    )
