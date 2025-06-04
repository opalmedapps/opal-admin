# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing model factories for Legacy database models."""

import datetime as dt
import json

from django.utils import timezone

from factory import Faker, Sequence, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory

from . import models


class LegacyUserFactory(DjangoModelFactory[models.LegacyUsers]):
    """Model factory for Legacy user."""

    class Meta:
        model = models.LegacyUsers

    usersernum = Sequence(lambda number: number + 1)
    usertypesernum = 51
    username = 'username'
    usertype = models.LegacyUserType.PATIENT


class LegacyPatientFactory(DjangoModelFactory[models.LegacyPatient]):
    """Model factory for Legacy Patient."""

    class Meta:
        model = models.LegacyPatient
        django_get_or_create = ('patientsernum',)

    patientsernum = 51
    first_name = 'Marge'
    last_name = 'Simpson'
    tel_num = '5149995555'
    date_of_birth = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    sex = 'Male'
    ramq = 'SIMM18510198'
    registration_date = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    language = 'EN'
    email = 'test@test.com'
    # All
    access_level = '3'
    last_updated = timezone.now()
    patient_aria_ser = Sequence(lambda number: number + 1)


class LegacyPatientControlFactory(DjangoModelFactory[models.LegacyPatientControl]):
    """Model factory for Legacy PatientControl."""

    class Meta:
        model = models.LegacyPatientControl
        django_get_or_create = ('patient',)

    patient = SubFactory(LegacyPatientFactory)
    patientupdate = 1
    lasttransferred = timezone.now()
    lastupdated = timezone.now()
    transferflag = 0


class LegacyNotificationFactory(DjangoModelFactory[models.LegacyNotification]):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyNotification

    readstatus = 0
    readby = '[]'
    patientsernum = SubFactory(LegacyPatientFactory)


class LegacyHospitalMapFactory(DjangoModelFactory[models.LegacyHospitalMap]):
    """HospitalMap factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyHospitalMap

    mapname_en = 'R720'
    mapname_fr = 'R720'
    dateadded = dt.datetime(2023, 3, 15, tzinfo=timezone.get_current_timezone())


class LegacyEducationalMaterialCategoryFactory(DjangoModelFactory[models.LegacyEducationalMaterialCategory]):
    """Educational material category from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterialCategory

    title_en = 'Clinical'


class LegacyEducationalMaterialControlFactory(DjangoModelFactory[models.LegacyEducationalMaterialControl]):
    """Educational material control factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterialControl

    educationalmaterialcategoryid = SubFactory(LegacyEducationalMaterialCategoryFactory)
    educational_material_type_en = 'Booklet'
    educational_material_type_fr = 'Brochure'
    publish_flag = 1
    name_en = 'Radiotherapy at the Cedars Cancer Centre'
    name_fr = 'Radiothérapie au Centre du Cancer des Cèdres'
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())


class LegacyAliasFactory(DjangoModelFactory[models.LegacyAlias]):
    """Alias factory from the legacy database."""

    class Meta:
        model = models.LegacyAlias

    aliastype = 'Appointment'
    aliasname_en = 'Calcul de la Dose'
    aliasname_fr = 'Calcul de la Dose'
    alias_description_en = 'Calcul de la Dose'
    alias_description_fr = 'Calcul de la Dose'
    educational_material_control_ser_num = SubFactory(LegacyEducationalMaterialControlFactory)
    hospitalmapsernum = SubFactory(LegacyHospitalMapFactory)


class LegacyMasterSourceAliasFactory(DjangoModelFactory[models.LegacyMasterSourceAlias]):
    """SourceDatabase factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyMasterSourceAlias

    external_id = Faker('pystr', max_chars=512)
    code = Faker('pystr', max_chars=128)
    description = Faker('pystr', max_chars=128)


class LegacySourceDatabaseFactory(DjangoModelFactory[models.LegacySourceDatabase]):
    """SourceDatabase factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacySourceDatabase

    source_database_name = Faker('word')
    enabled = True


class LegacyAliasExpressionFactory(DjangoModelFactory[models.LegacyAliasExpression]):
    """Legacy expression from legacy database."""

    class Meta:
        model = models.LegacyAliasExpression

    aliasexpressionsernum = Sequence(lambda number: number + 1)
    aliassernum = SubFactory(LegacyAliasFactory)
    master_source_alias_id = SubFactory(LegacyMasterSourceAliasFactory)
    description = Faker('sentence', nb_words=5)
    expression_name = Faker('sentence', nb_words=5)


class LegacyAppointmentFactory(DjangoModelFactory[models.LegacyAppointment]):
    """Model factory for Legacy notifications."""

    class Meta:
        model = models.LegacyAppointment

    scheduledstarttime = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    scheduled_end_time = dt.datetime(2018, 1, 2, tzinfo=timezone.get_current_timezone())
    checkin = 1
    status = 'Open'
    state = 'Active'
    readstatus = 0
    readby = '[]'
    roomlocation_en = 'CVIS Clinic Room 1'
    roomlocation_fr = 'SMVC Salle 1'
    aliasexpressionsernum = SubFactory(LegacyAliasExpressionFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    source_system_id = Sequence(lambda number: number + 1)
    last_updated = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    source_database = SubFactory(LegacySourceDatabaseFactory)


class LegacyDocumentFactory(DjangoModelFactory[models.LegacyDocument]):
    """Document factory from the legacy database."""

    class Meta:
        model = models.LegacyDocument

    documentsernum = Sequence(lambda number: number + 1)
    patientsernum = SubFactory(LegacyPatientFactory)
    sourcedatabasesernum = SubFactory(LegacySourceDatabaseFactory)
    documentid = '56190000000000039165511'
    aliasexpressionsernum = SubFactory(LegacyAliasExpressionFactory)
    approvedby = 890
    approvedtimestamp = dt.datetime(2023, 6, 1, 12, 36, tzinfo=timezone.get_current_timezone())
    authoredbysernum = 890
    dateofservice = dt.datetime(2023, 6, 8, 12, 35, tzinfo=timezone.get_current_timezone())
    revised = ''
    validentry = 'Y'
    originalfilename = 'bart_2009Feb23_pathology.pdf'
    finalfilename = 'bart_2009Feb23_pathology.pdf'
    createdbysernum = 890
    createdtimestamp = dt.datetime(2023, 6, 8, 12, 36, tzinfo=timezone.get_current_timezone())
    transferstatus = 'T'
    transferlog = 'Transfer successful'
    dateadded = dt.datetime(2023, 6, 9, 16, 38, 26, tzinfo=timezone.get_current_timezone())
    readstatus = 0
    readby = '[]'
    readstatus = 0


class LegacyTxTeamMessageFactory(DjangoModelFactory[models.LegacyTxTeamMessage]):
    """Txteammessage factory from the legacy database."""

    class Meta:
        model = models.LegacyTxTeamMessage

    patientsernum = SubFactory(LegacyPatientFactory)
    readby = '[]'
    readstatus = 0


class LegacyEducationalMaterialFactory(DjangoModelFactory[models.LegacyEducationalMaterial]):
    """Educational material factory from the legacy database."""

    class Meta:
        model = models.LegacyEducationalMaterial

    patientsernum = SubFactory(LegacyPatientFactory)
    educationalmaterialcontrolsernum = SubFactory(LegacyEducationalMaterialControlFactory)
    readby = '[]'
    readstatus = 0
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())


class LegacyQuestionnaireControlFactory(DjangoModelFactory[models.LegacyQuestionnaireControl]):
    """QuestionnaireControl factory from the legacy database."""

    class Meta:
        model = models.LegacyQuestionnaireControl

    questionnaire_db_ser_num = Faker('random_int', min=0, max=1000)
    questionnaire_name_en = 'Patient Satisfaction Questionnaire'
    questionnaire_name_fr = 'Questionnaire de satisfaction des patients'
    publish_flag = 1
    date_added = dt.datetime(2023, 6, 9, 16, 38, 26, tzinfo=timezone.get_current_timezone())


class LegacyQuestionnaireFactory(DjangoModelFactory[models.LegacyQuestionnaire]):
    """Questionnaire factory from the legacy database."""

    class Meta:
        model = models.LegacyQuestionnaire

    questionnaire_control_ser_num = SubFactory(LegacyQuestionnaireControlFactory)
    patientsernum = SubFactory(LegacyPatientFactory)
    patient_questionnaire_db_ser_num = Faker('random_int', min=0, max=1000)
    completedflag = 0
    date_added = dt.datetime(2023, 6, 9, 16, 38, 26, tzinfo=timezone.get_current_timezone())


class LegacyPostcontrolFactory(DjangoModelFactory[models.LegacyPostcontrol]):
    """Post Control factory for announcement from the legacy database."""

    posttype = 'Announcement'

    class Meta:
        model = models.LegacyPostcontrol


class LegacyAnnouncementFactory(DjangoModelFactory[models.LegacyAnnouncement]):
    """Announcement factory from the legacy database."""

    class Meta:
        model = models.LegacyAnnouncement

    patientsernum = SubFactory(LegacyPatientFactory)
    postcontrolsernum = SubFactory(LegacyPostcontrolFactory)
    readstatus = 0
    readby = '[]'


class LegacySecurityQuestionFactory(DjangoModelFactory[models.LegacySecurityQuestion]):
    """SecurityQuestion factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityQuestion

    securityquestionsernum = 1
    questiontext_en = 'What is the name of your first pet?'
    questiontext_fr = 'Quel est le nom de votre premier animal de compagnie?'
    creationdate = dt.datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    lastupdated = dt.datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    active = 1


class LegacySecurityAnswerFactory(DjangoModelFactory[models.LegacySecurityAnswer]):
    """SecurityAnswer factory from the legacy database."""

    class Meta:
        model = models.LegacySecurityAnswer

    securityanswersernum = 1
    securityquestionsernum = SubFactory(LegacySecurityQuestionFactory)
    patient = SubFactory(LegacyPatientFactory)
    answertext = 'bird'
    creationdate = dt.datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())
    lastupdated = dt.datetime(2022, 9, 27, tzinfo=timezone.get_current_timezone())


class LegacyPatientHospitalIdentifierFactory(DjangoModelFactory[models.LegacyPatientHospitalIdentifier]):
    """Patient_Hospital_Identifier factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyPatientHospitalIdentifier

    patient = SubFactory(LegacyPatientFactory)
    hospital = 'RVH'
    mrn = '9999996'
    is_active = True


class LegacyDiagnosisTranslationFactory(DjangoModelFactory[models.LegacyDiagnosisTranslation]):
    """DiagnosisTranslation factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosisTranslation

    name_en = Faker('sentence', nb_words=4)
    name_fr = Faker('sentence', nb_words=4)
    diagnosis_translation_ser_num = Sequence(lambda number: number + 1)


class LegacyDiagnosisCodeFactory(DjangoModelFactory[models.LegacyDiagnosisCode]):
    """Diagnosis factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosisCode

    description = Faker('sentence', nb_words=6)
    diagnosis_code = Faker('word')
    diagnosis_translation_ser_num = SubFactory(LegacyDiagnosisTranslationFactory)


class LegacyDiagnosisFactory(DjangoModelFactory[models.LegacyDiagnosis]):
    """Diagnosis factory from the legacy database OpalDB."""

    class Meta:
        model = models.LegacyDiagnosis

    patient_ser_num = SubFactory(LegacyPatientFactory)
    source_database = SubFactory(LegacySourceDatabaseFactory)
    diagnosis_aria_ser = '22234'
    diagnosis_code = 'C12.3'
    description_en = 'Breast Cancer'
    last_updated = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    stage = 'IIIB'
    stage_criteria = 'T2, pN1a, M0'
    creation_date = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())


class LegacyTestResultControlFactory(DjangoModelFactory[models.LegacyTestResultControl]):
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
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    last_published = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    last_updated_by = Sequence(lambda number: number)
    last_updated = timezone.now()
    url_en = Faker('url')
    url_fr = Faker('url')


class LegacyTestResultFactory(DjangoModelFactory[models.LegacyTestResult]):
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
    test_date = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    max_norm = Faker('pyfloat', positive=True)
    min_norm = Faker('pyfloat', positive=True)
    approved_flag = 'Y'
    test_value = Faker('pyfloat', positive=True)
    test_value_string = lazy_attribute(lambda legacytestresult: str(legacytestresult.test_value))
    unit_description = Faker('word')
    valid_entry = 'Y'
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    read_status = Faker('random_int', min=0, max=1)


class LegacyTestControlFactory(DjangoModelFactory[models.LegacyTestControl]):
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


class LegacyTestExpressionFactory(DjangoModelFactory[models.LegacyTestExpression]):
    """LegacyTestExpression factory."""

    class Meta:
        model = models.LegacyTestExpression

    test_code = Faker('random_int')
    test_control_ser_num = SubFactory(LegacyTestControlFactory)
    source_database = SubFactory(LegacySourceDatabaseFactory)
    expression_name = Faker('word')


class LegacyTestGroupExpressionFactory(DjangoModelFactory[models.LegacyTestGroupExpression]):
    """LegacyTestGroupExpression factory."""

    class Meta:
        model = models.LegacyTestGroupExpression

    test_code = Faker('random_int')
    source_database = SubFactory(LegacySourceDatabaseFactory)
    expression_name = Faker('word')


class LegacyPatientTestResultFactory(DjangoModelFactory[models.LegacyPatientTestResult]):
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
        lambda legacypatienttestresult: str(legacypatienttestresult.normal_range_min)
        + '-'
        + str(legacypatienttestresult.normal_range_max),
    )
    test_value_numeric = Faker('pyfloat', positive=True)
    test_value_string = lazy_attribute(lambda legacypatienttestresult: str(legacypatienttestresult.test_value_numeric))
    collected_date_time = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    result_date_time = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    unit_description = 'mmol'
    read_by = ''
    available_at = lazy_attribute(lambda _x: timezone.now())


class LegacyOARoleFactory(DjangoModelFactory[models.LegacyOARole]):
    """LegacyOARole factory."""

    class Meta:
        model = models.LegacyOARole

    name_en = Faker('name')
    name_fr = Faker('name')
    deleted_by = Faker('name')
    creation_date = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())
    created_by = Faker('name')
    updated_by = Faker('name')


class LegacyOAUserFactory(DjangoModelFactory[models.LegacyOAUser]):
    """LegacyOAUser factory."""

    class Meta:
        model = models.LegacyOAUser

    username = Faker('user_name')
    password = Faker('password')
    oa_role = SubFactory(LegacyOARoleFactory)
    date_added = dt.datetime(2018, 1, 1, tzinfo=timezone.get_current_timezone())


class LegacyOAUserRoleFactory(DjangoModelFactory[models.LegacyOAUserRole]):
    """LegacyOAUserRole factory."""

    class Meta:
        model = models.LegacyOAUserRole

    oausersernum = Faker('random_int')
    rolesernum = Faker('random_int')


class LegacyModuleFactory(DjangoModelFactory[models.LegacyModule]):
    """LegacyModule factory."""

    class Meta:
        model = models.LegacyModule
        django_get_or_create = ('name_en',)

    name_en = Faker('name')
    name_fr = Faker('name')
    description_en = Faker('sentence')
    description_fr = Faker('sentence')
    tablename = Faker('name')
    controltablename = Faker('name')
    primarykey = Faker('name')
    iconclass = Faker('name')
    url = Faker('url')
    sqlpublicationlist = Faker('paragraph')
    sqldetails = Faker('paragraph')
    sqlpublocationcharlog = Faker('paragraph')
    sqlpublicationlistlog = Faker('paragraph')
    sqlpublicationmultiple = Faker('paragraph')
    sqlpublicationunique = Faker('paragraph')


class LegacyOARoleModuleFactory(DjangoModelFactory[models.LegacyOARoleModule]):
    """LegacyOARoleModule factory."""

    class Meta:
        model = models.LegacyOARoleModule

    module = SubFactory(LegacyModuleFactory)
    oa_role = SubFactory(LegacyOARoleFactory)


class LegacyPatientActivityLogFactory(DjangoModelFactory[models.LegacyPatientActivityLog]):
    """LegacyPatientActivityLog factory."""

    class Meta:
        model = models.LegacyPatientActivityLog

    activity_ser_num = Sequence(lambda number: number + 1)
    # Possible request values:
    #   - AccountChange
    #   - DeviceIdentifier
    #   - DocumentContent
    #   - EducationalPackageContents
    #   - Feedback
    #   - GetOneItem
    #   - Log
    #   - Login
    #   - Logout
    #   - PatientTestDateResults
    #   - Questionnaire
    #   - QuestionnaireNumberUnread
    #   - QuestionnairePurpose
    #   - QuestionnaireSaveAnswer
    #   - QuestionnaireUpdateStatus
    #   - Read
    #   - Refresh
    #   - SecurityQuestion
    #   - SecurityQuestionAnswerList
    #   - UpdateSecurityQuestionAnswer
    #   - VerifyAnswer
    #   etc.
    request = 'Log'
    parameters = json.dumps(
        {
            'Activity': 'Login',
            'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
        },
        separators=(',', ':'),
    )
    target_patient_id = 51
    username = Faker('user_name')
    device_id = Faker('uuid4')
    session_id = ''
    date_time = timezone.now() - dt.timedelta(days=1)
    lastupdated = timezone.now() - dt.timedelta(days=1)
    app_version = '100.100.100'


class LegacyPatientDeviceIdentifierFactory(DjangoModelFactory[models.LegacyPatientDeviceIdentifier]):
    """LegacyPatientDeviceIdentifier factory."""

    class Meta:
        model = models.LegacyPatientDeviceIdentifier

    patient_device_identifier_ser_num = Sequence(lambda number: number + 1)
    device_id = Faker('uuid4')
    app_version = '100.100.100'
    registration_id = ''
    device_type = 0
    security_answer_ser_num = None
    attempt = 0
    trusted = 1
    timeout_timestamp = None
    last_updated = timezone.now()
    username = Faker('user_name')
    security_answer = Faker('uuid4')
