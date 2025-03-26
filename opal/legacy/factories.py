"""Module providing model factories for Legacy database models."""
from datetime import datetime

from django.utils import timezone

from factory import Faker, Sequence, SubFactory, lazy_attribute
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
    firstname = 'Marge'
    lastname = 'Simpson'
    telnum = '5149995555'
    dateofbirth = timezone.make_aware(datetime(2018, 1, 1))
    sex = 'Male'
    ssn = '123456'
    registrationdate = timezone.make_aware(datetime(2018, 1, 1))
    language = 'EN'
    email = 'test@test.com'
    # All
    accesslevel = '3'
    last_updated = timezone.now()
    patient_aria_ser = Sequence(lambda number: number + 1)


class LegacyNotificationFactory(DjangoModelFactory):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyNotification

    readstatus = 0
    readby = '[]'
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyHospitalMapFactory(DjangoModelFactory):
    """HospitalMap factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyHospitalMap

    mapname_en = 'R720'
    mapname_fr = 'R720'
    dateadded = timezone.make_aware(datetime(2023, 3, 15))


class LegacyAliasFactory(DjangoModelFactory):
    """Alias factory from the legacy database."""

    class Meta:
        model = models.LegacyAlias

    aliastype = 'Appointment'
    aliasname_en = 'Calcul de la Dose'
    aliasname_fr = 'Calcul de la Dose'
    alias_description_en = 'Calcul de la Dose'
    alias_description_fr = 'Calcul de la Dose'
    hospitalmapsernum = SubFactory(LegacyHospitalMapFactory)


class LegacyMasterSourceAliasFactory(DjangoModelFactory):
    """SourceDatabase factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyMasterSourceAlias

    external_id = Faker('pystr', max_chars=512)
    code = Faker('pystr', max_chars=128)
    description = Faker('pystr', max_chars=128)


class LegacySourceDatabaseFactory(DjangoModelFactory):
    """SourceDatabase factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacySourceDatabase

    source_database_name = Faker('word')
    enabled = True


class LegacyAliasExpressionFactory(DjangoModelFactory):
    """Legacy expression from legacy database."""

    class Meta:
        model = models.LegacyAliasExpression

    aliasexpressionsernum = Sequence(lambda number: number + 1)
    aliassernum = SubFactory(LegacyAliasFactory)
    master_source_alias_id = SubFactory(LegacyMasterSourceAliasFactory)
    description = Faker('sentence', nb_words=5)
    expression_name = Faker('sentence', nb_words=5)


class LegacyAppointmentFactory(DjangoModelFactory):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyAppointment

    scheduledstarttime = timezone.make_aware(datetime(2018, 1, 1))
    scheduled_end_time = timezone.make_aware(datetime(2018, 1, 2))
    checkin = 1
    status = 'Open'
    state = 'active'
    readstatus = 0
    readby = '[]'
    roomlocation_en = 'CVIS Clinic Room 1'
    roomlocation_fr = 'SMVC Salle 1'
    aliasexpressionsernum = SubFactory(LegacyAliasExpressionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
    date_added = timezone.make_aware(datetime(2018, 1, 1))
    appointment_aria_ser = Sequence(lambda number: number + 1)
    last_updated = timezone.make_aware(datetime(2018, 1, 1))
    source_database = SubFactory(LegacySourceDatabaseFactory)


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


class LegacyEducationalMaterialCategoryFactory(DjangoModelFactory):
    """Educational material category from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterialCategory

    title_en = 'Clinical'


class LegacyEducationalMaterialControlFactory(DjangoModelFactory):
    """Educational material control factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterialControl

    educationalmaterialcategoryid = SubFactory(LegacyEducationalMaterialCategoryFactory)


class LegacyEducationalMaterialFactory(DjangoModelFactory):
    """Educational material factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterial

    patientsernum = SubFactory(LegacyPatientFactory)
    educationalmaterialcontrolsernum = SubFactory(LegacyEducationalMaterialControlFactory)
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


class LegacyDiagnosisTranslationFactory(DjangoModelFactory):
    """DiagnosisTranslation factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosisTranslation

    name_en = Faker('sentence', nb_words=4)
    name_fr = Faker('sentence', nb_words=4)
    diagnosis_translation_ser_num = Sequence(lambda number: number + 1)


class LegacyDiagnosisCodeFactory(DjangoModelFactory):
    """Diagnosis factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosisCode

    description = Faker('sentence', nb_words=6)
    diagnosis_code = Faker('word')
    diagnosis_translation_ser_num = SubFactory(LegacyDiagnosisTranslationFactory)


class LegacyDiagnosisFactory(DjangoModelFactory):
    """Diagnosis factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosis

    patient_ser_num = SubFactory(LegacyPatientFactory)
    source_database = SubFactory(LegacySourceDatabaseFactory)
    diagnosis_aria_ser = '22234'
    diagnosis_code = 'C12.3'
    description_en = 'Breast Cancer'
    last_updated = timezone.make_aware(datetime(2018, 1, 1))
    stage = 'IIIB'
    stage_criteria = 'T2, pN1a, M0'
    creation_date = timezone.make_aware(datetime(2018, 1, 1))


class LegacyTestResultControlFactory(DjangoModelFactory):
    """TestResultControl factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyTestResultControl

    name_en = Faker('sentence', nb_words=5)
    name_fr = Faker('sentence', nb_words=5)
    description_en = Faker('paragraph', nb_sentences=3)
    description_fr = Faker('paragraph', nb_sentences=3)
    group_en = Faker('word')
    group_fr = Faker('word')
    source_database = 1
    publish_flag = Sequence(lambda number: number)
    date_added = timezone.make_aware(datetime(2018, 1, 1))
    last_published = timezone.make_aware(datetime(2018, 1, 1))
    last_updated_by = Sequence(lambda number: number)
    last_updated = datetime.now()
    url_en = Faker('url')
    url_fr = Faker('url')


class LegacyTestResultFactory(DjangoModelFactory):
    """TestResultControl factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyTestResult

    test_result_group_ser_num = Sequence(lambda number: number + 1)
    test_result_control_ser_num = SubFactory(LegacyTestResultControlFactory)
    test_result_expression_ser_num = Sequence(lambda number: number + 1)
    patient_ser_num = SubFactory(LegacyPatientFactory)
    source_database = SubFactory(LegacySourceDatabaseFactory)
    test_result_aria_ser = Faker('word')
    component_name = Faker('word')
    fac_component_name = Faker('word')
    abnormal_flag = 'N'
    test_date = timezone.make_aware(datetime(2018, 1, 1))
    max_norm = Faker('pyfloat', positive=True)
    min_norm = Faker('pyfloat', positive=True)
    approved_flag = 'Y'
    test_value = Faker('pyfloat', positive=True)
    test_value_string = lazy_attribute(lambda legacytestresult: str(legacytestresult.test_value))
    unit_description = Faker('word')
    valid_entry = 'Y'
    date_added = timezone.make_aware(datetime(2018, 1, 1))
    read_status = Faker('random_int', min=0, max=1)


class LegacyTestControlFactory(DjangoModelFactory):
    """LegacyTestControl factory."""

    class Meta:
        model = models.LegacyTestControl

    name_en = Faker('name')
    name_fr = Faker('name')
    group_en = Faker('name')
    group_fr = Faker('name')
    description_en = Faker('name')
    description_fr = Faker('name')
    source_database = SubFactory(LegacySourceDatabaseFactory)
    educational_material_control_ser_num = SubFactory(LegacyEducationalMaterialControlFactory)
    publish_flag = 1
    url_en = Faker('url')
    url_fr = Faker('url')


class LegacyTestExpressionFactory(DjangoModelFactory):
    """LegacyTestExpression factory."""

    class Meta:
        model = models.LegacyTestExpression

    test_code = Faker('random_int')
    test_control_ser_num = SubFactory(LegacyTestControlFactory)
    source_database = SubFactory(LegacySourceDatabaseFactory)
    expression_name = Faker('word')


class LegacyTestGroupExpressionFactory(DjangoModelFactory):
    """LegacyTestGroupExpression factory."""

    class Meta:
        model = models.LegacyTestGroupExpression

    test_code = Faker('random_int')
    source_database = SubFactory(LegacySourceDatabaseFactory)
    expression_name = Faker('word')


class LegacyPatientTestResultFactory(DjangoModelFactory):
    """LegacyPatientTestResult factory."""

    class Meta:
        model = models.LegacyPatientTestResult

    patient_ser_num = SubFactory(LegacyPatientFactory)
    test_group_expression_ser_num = SubFactory(LegacyTestGroupExpressionFactory)
    test_expression_ser_num = SubFactory(LegacyTestExpressionFactory)
    abnormal_flag = Faker('random_int')
    sequence_num = Faker('random_int')
    normal_range_min = Faker('random_int')
    normal_range_max = Faker('random_int')
    normal_range = lazy_attribute(
        lambda legacypatienttestresult:
        str(legacypatienttestresult.normal_range_min)
        + '-'
        + str(legacypatienttestresult.normal_range_max),
    )
    test_value_numeric = Faker('pyfloat', positive=True)
    test_value_string = lazy_attribute(lambda legacypatienttestresult: str(legacypatienttestresult.test_value_numeric))
    collected_date_time = timezone.make_aware(datetime(2018, 1, 1))
    result_date_time = timezone.make_aware(datetime(2018, 1, 1))
    unit_description = 'mmol'
    read_by = ''


class LegacyOARoleFactory(DjangoModelFactory):
    """LegacyOARole factory."""

    class Meta:
        model = models.LegacyOARole

    name_en = Faker('name')
    name_fr = Faker('name')
    deletedby = Faker('name')
    creationdate = timezone.make_aware(datetime(2018, 1, 1))
    createdby = Faker('name')
    updatedby = Faker('name')


class LegacyOAUserFactory(DjangoModelFactory):
    """LegacyOAUser factory."""

    class Meta:
        model = models.LegacyOAUser

    username = Faker('user_name')
    password = Faker('password')
    oaroleid = SubFactory(LegacyOARoleFactory)
    date_added = timezone.make_aware(datetime(2018, 1, 1))


class LegacyOAUserRoleFactory(DjangoModelFactory):
    """LegacyOAUserRole factory."""

    class Meta:
        model = models.LegacyOAUserRole

    oausersernum = Faker('random_int')
    rolesernum = Faker('random_int')


class LegacyModuleFactory(DjangoModelFactory):
    """LegacyModule factory."""

    class Meta:
        model = models.LegacyModule

    name_en = Faker('name')
    name_fr = Faker('name')


class LegacyOARoleModuleFactory(DjangoModelFactory):
    """LegacyOARoleModule factory."""

    class Meta:
        model = models.LegacyOARoleModule

    moduleid = SubFactory(LegacyModuleFactory)
    oaroleid = SubFactory(LegacyOARoleFactory)
