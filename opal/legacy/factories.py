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
    firstname = 'TEST'
    lastname = 'LEGACY'
    telnum = '5149995555'
    dateofbirth = timezone.make_aware(datetime(2018, 1, 1))
    sex = 'Male'
    ssn = '123456'
    registrationdate = timezone.make_aware(datetime(2018, 1, 1))
    language = 'EN'
    email = 'test@test.com'


class LegacyNotificationFactory(DjangoModelFactory):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyNotification

    readstatus = 0
    readby = '[]'
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyAliasFactory(DjangoModelFactory):
    """Alias factory from the legacy database."""

    class Meta:
        model = models.LegacyAlias

    aliassernum = 283
    aliastype = 'Appointment'
    aliasname_en = 'Calcul de la Dose'
    aliasname_fr = 'Calcul de la Dose'


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
    readby = '[]'
    roomlocation_en = 'CVIS Clinic Room 1'
    roomlocation_fr = 'SMVC Salle 1'
    aliasexpressionsernum = SubFactory(LegacyAliasexpressionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyDocumentFactory(DjangoModelFactory):
    """Document factory from the legacy database."""

    class Meta:
        model = models.LegacyDocument

    patientsernum = SubFactory(LegacyPatientFactory)
    readby = '[]'
    readstatus = 0


class LegacyTxTeamMessageFactory(DjangoModelFactory):
    """Txteammessage factory from the legacy database."""

    class Meta:
        model = models.LegacyTxTeamMessage

    patientsernum = SubFactory(LegacyPatientFactory)
    readby = '[]'
    readstatus = 0


class LegacyEducationalMaterialFactory(DjangoModelFactory):
    """Educational material factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterial

    patientsernum = SubFactory(LegacyPatientFactory)
    readby = '[]'
    readstatus = 0


class LegacyQuestionnaireFactory(DjangoModelFactory):
    """Questionnaire factory from the legacy database."""

    class Meta:
        model = models.LegacyQuestionnaire

    patientsernum = SubFactory(LegacyPatientFactory)
    completedflag = 0


class LegacyPostcontrolFactory(DjangoModelFactory):
    """Post Controle factory for announcement from the legacy database."""

    class Meta:
        model = models.LegacyPostcontrol


class LegacyAnnouncementFactory(DjangoModelFactory):
    """Announcement factory from the legacy database."""

    class Meta:
        model = models.LegacyAnnouncement

    patientsernum = SubFactory(LegacyPatientFactory)
    postcontrolsernum = SubFactory(LegacyPostcontrolFactory)
    readstatus = 0
    readby = '[]'


class LegacySecurityQuestionFactory(DjangoModelFactory):
    """SecurityQuestion factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityQuestion

    securityquestionsernum = 1
    questiontext_en = 'What is the name of your first pet?'
    questiontext_fr = 'Quel est le nom de votre premier animal de compagnie?'
    creationdate = timezone.make_aware(datetime(2022, 9, 27))
    lastupdated = timezone.make_aware(datetime(2022, 9, 27))
    active = 1


class LegacySecurityAnswerFactory(DjangoModelFactory):
    """SecurityAnswer factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityAnswer

    securityanswersernum = 1
    securityquestionsernum = SubFactory(LegacySecurityQuestionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
    answertext = 'bird'
    creationdate = timezone.make_aware(datetime(2022, 9, 27))
    lastupdated = timezone.make_aware(datetime(2022, 9, 27))


class LegacyHospitalIdentifierTypeFactory(DjangoModelFactory):
    """Hospital_Identifier_Type factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyHospitalIdentifierType

    code = 'RVH'


class LegacyPatientHospitalIdentifierFactory(DjangoModelFactory):
    """Patient_Hospital_Identifier factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyPatientHospitalIdentifier

    patientsernum = SubFactory(LegacyPatientFactory)
    hospitalidentifiertypecode = SubFactory(LegacyHospitalIdentifierTypeFactory)
    mrn = '9999996'
    isactive = True


class LegacyHospitalMapFactory(DjangoModelFactory):
    """HospitalMap factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyHospitalMap

    hospitalmapsernum = 1
    mapname_en = 'R720'
    mapname_fr = 'R720'
    dateadded = timezone.make_aware(datetime(2023, 3, 15))
