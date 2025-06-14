# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module providing legacy models to provide access to the legacy DB.

Each model in this module should be prefixed with `Legacy`
and have its `Meta.managed` property set to `False`.

If a model is only used for read operations, the model may contain only those fields that are needed.

When inspecting an existing database table using `inspectdb`, make sure of the following:

* Rename the model and prefix with `Legacy`
* Ensure `Meta.managed` is set to False
* Rearrange the models order if necessary (e.g., when there are foreign keys between them)
* Make sure each model has one field with primary_key=True
* Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
* Don't rename db_table or db_column values
"""

import datetime as dt

from django.db import models
from django.utils import timezone

from . import managers


class LegacyUserType(models.TextChoices):
    """The possible user type values."""

    PATIENT = 'Patient'
    CAREGIVER = 'Caregiver'


class LegacyUsers(models.Model):
    """User model from the legacy database OpalDB."""

    usersernum = models.AutoField(db_column='UserSerNum', primary_key=True)
    usertype = models.CharField(db_column='UserType', max_length=255, choices=LegacyUserType.choices)
    usertypesernum = models.IntegerField(db_column='UserTypeSerNum')
    username = models.CharField(db_column='Username', max_length=255)
    password = models.CharField(db_column='Password', max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = 'Users'


class LegacySexType(models.TextChoices):
    """The possible sex values for a patient."""

    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'
    UNKNOWN = 'Unknown'


class LegacyLanguage(models.TextChoices):
    """The possible language values."""

    ENGLISH = 'EN'
    FRENCH = 'FR'


class LegacyAccessLevel(models.TextChoices):
    """The possible access level values."""

    NEED_TO_KNOW = '1'
    ALL = '3'


class LegacyPatient(models.Model):
    """Patient model from the legacy database."""

    patientsernum = models.AutoField(db_column='PatientSerNum', primary_key=True)
    first_name = models.CharField(db_column='FirstName', max_length=50)
    last_name = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', max_length=50, blank=True)
    registration_date = models.DateTimeField(db_column='RegistrationDate', auto_now_add=True)
    language = models.CharField(
        db_column='Language',
        max_length=2,
        choices=LegacyLanguage.choices,
    )
    tel_num = models.BigIntegerField(db_column='TelNum', blank=True, null=True)
    date_of_birth = models.DateTimeField(db_column='DateOfBirth')
    death_date = models.DateTimeField(db_column='DeathDate', blank=True, null=True)
    ramq = models.CharField(db_column='SSN', max_length=16, blank=True)
    access_level = models.CharField(
        db_column='AccessLevel',
        max_length=1,
        default=LegacyAccessLevel.NEED_TO_KNOW,
        choices=LegacyAccessLevel.choices,
    )
    sex = models.CharField(db_column='Sex', max_length=25, choices=LegacySexType.choices)
    age = models.IntegerField(db_column='Age', blank=True, null=True)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    patient_aria_ser = models.IntegerField(db_column='PatientAriaSer', default=0)

    objects: managers.LegacyPatientManager = managers.LegacyPatientManager()

    class Meta:
        managed = False
        db_table = 'Patient'


class LegacyPatientControl(models.Model):
    """Patient control from the legacy database."""

    patient = models.OneToOneField('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum', primary_key=True)
    patientupdate = models.IntegerField(db_column='PatientUpdate', default=1)
    lasttransferred = models.DateTimeField(
        db_column='LastTransferred',
        default=dt.datetime(2000, 1, 1, tzinfo=timezone.get_current_timezone()),
    )
    lastupdated = models.DateTimeField(db_column='LastUpdated', auto_now_add=True)
    transferflag = models.SmallIntegerField(db_column='TransferFlag', default=0)

    class Meta:
        managed = False
        db_table = 'PatientControl'


class LegacyNotification(models.Model):
    """Notification model from the legacy database OpalDB."""

    notificationsernum = models.AutoField(db_column='NotificationSerNum', primary_key=True)
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
    objects: managers.LegacyNotificationManager = managers.LegacyNotificationManager()

    class Meta:
        managed = False
        db_table = 'Notification'


class LegacySourceDatabase(models.Model):
    """SourceDatabase from the legacy database OpalDB."""

    source_database = models.AutoField(db_column='SourceDatabaseSerNum', primary_key=True)
    source_database_name = models.CharField(db_column='SourceDatabaseName', max_length=255)
    enabled = models.SmallIntegerField(db_column='Enabled')

    class Meta:
        managed = False
        db_table = 'SourceDatabase'


class LegacyAppointment(models.Model):
    """Class to get appointment information from the legacy database."""

    appointmentsernum = models.AutoField(db_column='AppointmentSerNum', primary_key=True)
    aliasexpressionsernum = models.ForeignKey(
        'LegacyAliasExpression',
        models.DO_NOTHING,
        db_column='AliasExpressionSerNum',
        to_field='aliasexpressionsernum',
    )
    patientsernum = models.ForeignKey(
        'LegacyPatient',
        models.DO_NOTHING,
        db_column='PatientSerNum',
        to_field='patientsernum',
    )
    state = models.CharField(db_column='State', max_length=25)
    scheduledstarttime = models.DateTimeField(db_column='ScheduledStartTime')
    checkin = models.IntegerField(db_column='Checkin')
    status = models.CharField(db_column='Status', max_length=100)
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
    roomlocation_en = models.CharField(db_column='RoomLocation_EN', max_length=100)
    roomlocation_fr = models.CharField(db_column='RoomLocation_FR', max_length=100)
    date_added = models.DateTimeField(db_column='DateAdded')
    scheduled_end_time = models.DateTimeField(db_column='ScheduledEndTime')
    source_system_id = models.CharField(db_column='SourceSystemID', max_length=100)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    source_database = models.ForeignKey(
        'LegacySourceDatabase',
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )

    objects: managers.LegacyAppointmentManager = managers.LegacyAppointmentManager()

    class Meta:
        managed = False
        db_table = 'Appointment'


class LegacyAliasExpression(models.Model):
    """Legcy alias expression model mapping AliasExpression table from legacy database."""

    aliasexpressionsernum = models.AutoField(db_column='AliasExpressionSerNum', primary_key=True)
    aliassernum = models.ForeignKey(
        'LegacyAlias',
        models.DO_NOTHING,
        db_column='AliasSerNum',
        to_field='aliassernum',
    )
    expression_name = models.CharField(db_column='ExpressionName', max_length=250)
    description = models.CharField(db_column='Description', max_length=250)
    master_source_alias_id = models.ForeignKey(
        'LegacyMasterSourceAlias',
        models.DO_NOTHING,
        db_column='masterSourceAliasId',
        to_field='id',
    )

    class Meta:
        managed = False
        db_table = 'AliasExpression'


class LegacyAlias(models.Model):
    """Legacy alias model mapping Alias table from legacy database."""

    aliassernum = models.AutoField(db_column='AliasSerNum', primary_key=True)
    aliastype = models.CharField(db_column='AliasType', max_length=25)
    aliasname_en = models.CharField(db_column='AliasName_EN', max_length=100)
    aliasname_fr = models.CharField(db_column='AliasName_FR', max_length=100)
    hospitalmapsernum = models.ForeignKey(
        'LegacyHospitalMap',
        models.DO_NOTHING,
        db_column='HospitalMapSerNum',
        blank=True,
        null=True,
    )
    alias_description_en = models.TextField(db_column='AliasDescription_EN')
    alias_description_fr = models.TextField(db_column='AliasDescription_FR')
    # TODO To be renamed to Reference Material when fully migrated to Django
    educational_material_control_ser_num = models.ForeignKey(
        'LegacyEducationalMaterialControl',
        models.DO_NOTHING,
        db_column='EducationalMaterialControlSerNum',
        to_field='educationalmaterialcontrolsernum',
        null=True,
    )

    class Meta:
        managed = False
        db_table = 'Alias'


class LegacyAppointmentcheckin(models.Model):
    """Legacy appointment checkin mapping appointment checkin table from the legacy database."""

    aliassernum = models.OneToOneField(
        'LegacyAlias',
        models.DO_NOTHING,
        db_column='AliasSerNum',
        primary_key=True,
        related_name='appointmentcheckin',
    )
    checkinpossible = models.IntegerField(db_column='CheckinPossible')
    checkininstruction_en = models.TextField(db_column='CheckinInstruction_EN')
    checkininstruction_fr = models.TextField(db_column='CheckinInstruction_FR')

    class Meta:
        managed = False
        db_table = 'AppointmentCheckin'


class LegacyDocument(models.Model):
    """Document model from the legacy database OpalDB."""

    documentsernum = models.AutoField(db_column='DocumentSerNum', primary_key=True)
    # TODO: add cronlogsernum
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    sourcedatabasesernum = models.ForeignKey(
        to=LegacySourceDatabase,
        on_delete=models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    documentid = models.CharField(db_column='DocumentId', blank=True, max_length=100)
    aliasexpressionsernum = models.ForeignKey(
        to=LegacyAliasExpression,
        on_delete=models.DO_NOTHING,
        db_column='AliasExpressionSerNum',
        to_field='aliasexpressionsernum',
    )
    approvedby = models.IntegerField(db_column='ApprovedBySerNum')
    approvedtimestamp = models.DateTimeField(db_column='ApprovedTimeStamp')
    authoredbysernum = models.IntegerField(db_column='AuthoredBySerNum')
    dateofservice = models.DateTimeField(db_column='DateOfService')
    revised = models.CharField(db_column='Revised', blank=True, max_length=5)
    validentry = models.CharField(db_column='ValidEntry', max_length=5)
    errorreasontext = models.TextField(db_column='ErrorReasonText', blank=True)
    originalfilename = models.CharField(db_column='OriginalFileName', max_length=500)
    finalfilename = models.CharField(db_column='FinalFileName', max_length=500)
    createdbysernum = models.IntegerField(db_column='CreatedBySerNum')
    createdtimestamp = models.DateTimeField(db_column='CreatedTimeStamp')
    transferstatus = models.CharField(db_column='TransferStatus', max_length=10)
    transferlog = models.CharField(db_column='TransferLog', max_length=1000)
    sessionid = models.TextField(db_column='SessionId', blank=True)
    dateadded = models.DateTimeField(db_column='DateAdded')
    readstatus = models.IntegerField(
        db_column='ReadStatus',
        help_text='Deprecated',
    )
    readby = models.JSONField(db_column='ReadBy', default=list)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    objects: managers.LegacyDocumentManager = managers.LegacyDocumentManager()

    class Meta:
        managed = False
        db_table = 'Document'


class LegacyTxTeamMessage(models.Model):
    """Txteammessage model from the legacy database OpalDB."""

    txteammessagesernum = models.AutoField(db_column='TxTeamMessageSerNum', primary_key=True)
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
    objects: managers.LegacyTxTeamMessageManager = managers.LegacyTxTeamMessageManager()

    class Meta:
        managed = False
        db_table = 'TxTeamMessage'


class LegacyEducationalMaterial(models.Model):
    """Educationalmaterial model from the legacy database OpalDB."""

    educationalmaterialsernum = models.AutoField(db_column='EducationalMaterialSerNum', primary_key=True)
    educationalmaterialcontrolsernum = models.ForeignKey(
        'LegacyEducationalMaterialControl',
        models.DO_NOTHING,
        db_column='EducationalMaterialControlSerNum',
    )
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
    date_added = models.DateTimeField(db_column='DateAdded')
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    objects: managers.LegacyEducationalMaterialManager = managers.LegacyEducationalMaterialManager()

    class Meta:
        managed = False
        db_table = 'EducationalMaterial'


class LegacyEducationalMaterialControl(models.Model):
    """EducationalMaterialControl model from the legacy database OpalDB."""

    educationalmaterialcontrolsernum = models.AutoField(db_column='EducationalMaterialControlSerNum', primary_key=True)
    educational_material_type_en = models.CharField(max_length=100, db_column='EducationalMaterialType_EN')
    educational_material_type_fr = models.CharField(max_length=100, db_column='EducationalMaterialType_FR')
    publish_flag = models.IntegerField(db_column='PublishFlag', default=0)
    name_en = models.CharField(db_column='Name_EN', max_length=200)
    name_fr = models.CharField(db_column='Name_FR', max_length=200)
    date_added = models.DateTimeField(db_column='DateAdded')
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    educationalmaterialcategoryid = models.ForeignKey(
        'LegacyEducationalMaterialCategory',
        models.DO_NOTHING,
        db_column='EducationalMaterialCategoryId',
    )
    # These columns are configured to allow NULL in the database
    url_en = models.CharField(db_column='URL_EN', max_length=2000, null=True, blank=True)
    url_fr = models.CharField(db_column='URL_FR', max_length=2000, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'EducationalMaterialControl'


class LegacyEducationalMaterialCategory(models.Model):
    """EducationalMaterialCategory model from the legacy database OpalDB."""

    id = models.AutoField(db_column='ID', primary_key=True)
    title_en = models.CharField(db_column='title_EN', max_length=128)
    title_fr = models.CharField(db_column='title_FR', max_length=128)

    class Meta:
        managed = False
        db_table = 'EducationalMaterialCategory'


class LegacyQuestionnaire(models.Model):
    """Questionnaire model from the legacy database OpalDB."""

    questionnairesernum = models.BigAutoField(db_column='QuestionnaireSerNum', primary_key=True)
    questionnaire_control_ser_num = models.ForeignKey(
        'LegacyQuestionnaireControl',
        models.DO_NOTHING,
        db_column='QuestionnaireControlSerNum',
        to_field='questionnaire_control_ser_num',
    )
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    patient_questionnaire_db_ser_num = models.IntegerField(db_column='PatientQuestionnaireDBSerNum')
    completedflag = models.IntegerField(db_column='CompletedFlag')
    date_added = models.DateTimeField(db_column='DateAdded')
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    objects: managers.LegacyQuestionnaireManager = managers.LegacyQuestionnaireManager()

    class Meta:
        managed = False
        db_table = 'Questionnaire'


class LegacyQuestionnaireControl(models.Model):
    """QuestionnaireControl model from the legacy database OpalDB."""

    questionnaire_control_ser_num = models.BigAutoField(db_column='QuestionnaireControlSerNum', primary_key=True)
    questionnaire_db_ser_num = models.IntegerField(db_column='QuestionnaireDBSerNum')
    questionnaire_name_en = models.CharField(db_column='QuestionnaireName_EN', max_length=2056)
    questionnaire_name_fr = models.CharField(db_column='QuestionnaireName_FR', max_length=2056)
    publish_flag = models.SmallIntegerField(db_column='PublishFlag')
    date_added = models.DateTimeField(db_column='DateAdded')
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'QuestionnaireControl'


class LegacyAnnouncement(models.Model):
    """Announcement model from the legacy database OpalDB."""

    announcementsernum = models.AutoField(db_column='AnnouncementSerNum', primary_key=True)
    postcontrolsernum = models.ForeignKey(
        'LegacyPostcontrol',
        models.DO_NOTHING,
        db_column='PostControlSerNum',
        to_field='postcontrolsernum',
    )
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
    objects: managers.LegacyAnnouncementManager = managers.LegacyAnnouncementManager()

    class Meta:
        managed = False
        db_table = 'Announcement'


class LegacyPostcontrol(models.Model):
    """PostControl model from the legacy database OpalDB."""

    postcontrolsernum = models.AutoField(db_column='PostControlSerNum', primary_key=True)
    posttype = models.CharField(db_column='PostType', max_length=100)

    class Meta:
        managed = False
        db_table = 'PostControl'


class LegacySecurityQuestion(models.Model):
    """Securityquestion model from the legacy database OpalDB."""

    securityquestionsernum = models.AutoField(db_column='SecurityQuestionSerNum', primary_key=True)
    questiontext_en = models.CharField(db_column='QuestionText_EN', max_length=2056)
    questiontext_fr = models.CharField(db_column='QuestionText_FR', max_length=2056)
    creationdate = models.DateTimeField(db_column='CreationDate')
    lastupdated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    active = models.IntegerField(db_column='Active')

    class Meta:
        managed = False
        db_table = 'SecurityQuestion'


class LegacySecurityAnswer(models.Model):
    """SecurityAnswer model from the legacy database OpalDB."""

    securityanswersernum = models.AutoField(db_column='SecurityAnswerSerNum', primary_key=True)
    securityquestionsernum = models.ForeignKey(
        'LegacySecurityquestion',
        models.DO_NOTHING,
        db_column='SecurityQuestionSerNum',
    )
    patient = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    answertext = models.CharField(db_column='AnswerText', max_length=2056)
    creationdate = models.DateTimeField(db_column='CreationDate')
    lastupdated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'SecurityAnswer'
        unique_together = (('securityquestionsernum', 'patient'),)


class LegacyHospitalIdentifierType(models.Model):
    """Hospital_Identifier_Type model from the legacy database OpalDB."""

    hospitalidentifiertypeid = models.AutoField(db_column='Hospital_Identifier_Type_Id', primary_key=True)
    code = models.CharField(db_column='Code', max_length=20, unique=True)

    class Meta:
        managed = False
        db_table = 'Hospital_Identifier_Type'


class LegacyPatientHospitalIdentifier(models.Model):
    """Patient_Hospital_Identifier model from the legacy database OpalDB."""

    patienthospitalidentifierid = models.AutoField(db_column='Patient_Hospital_Identifier_Id', primary_key=True)
    patient = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    hospital = models.CharField(db_column='Hospital_Identifier_Type_Code', max_length=20)
    mrn = models.CharField(db_column='MRN', max_length=20)
    is_active = models.BooleanField(db_column='is_Active')

    class Meta:
        managed = False
        db_table = 'Patient_Hospital_Identifier'
        unique_together = (('patient', 'hospital', 'mrn'),)


class LegacyHospitalMap(models.Model):
    """Hospital_Map model from the legacy database OpalDB."""

    hospitalmapsernum = models.AutoField(db_column='HospitalMapSerNum', primary_key=True)
    mapurl_en = models.CharField(db_column='MapURL_EN', max_length=255)
    mapurl_fr = models.CharField(db_column='MapURL_FR', max_length=255)
    mapname_en = models.CharField(db_column='MapName_EN', max_length=255)
    mapname_fr = models.CharField(db_column='MapName_FR', max_length=255)
    mapdescription_en = models.CharField(db_column='MapDescription_EN', max_length=255)
    mapdescription_fr = models.CharField(db_column='MapDescription_FR', max_length=255)
    dateadded = models.DateTimeField(db_column='DateAdded')
    sessionid = models.CharField(db_column='SessionId', max_length=255)

    class Meta:
        managed = False
        db_table = 'HospitalMap'


class LegacyMasterSourceAlias(models.Model):
    """MasterSourceAlias from the legacy database OpalDB."""

    id = models.AutoField(primary_key=True, db_column='ID')
    external_id = models.CharField(db_column='externalId', max_length=512)
    code = models.CharField(db_column='code', max_length=128)
    description = models.CharField(db_column='description', max_length=128)

    class Meta:
        managed = False
        db_table = 'masterSourceAlias'


class LegacyDiagnosisTranslation(models.Model):
    """DiagnosisTranslation from the legacy database OpalDB."""

    diagnosis_translation_ser_num = models.AutoField(db_column='DiagnosisTranslationSerNum', primary_key=True)
    name_en = models.CharField(db_column='Name_EN', max_length=2056)
    name_fr = models.CharField(db_column='Name_FR', max_length=2056)

    class Meta:
        managed = False
        db_table = 'DiagnosisTranslation'


class LegacyDiagnosisCode(models.Model):
    """DiagnosisCode from the legacy database OpalDB."""

    diagnosis_code_ser_num = models.AutoField(primary_key=True, db_column='DiagnosisCodeSerNum')
    diagnosis_translation_ser_num = models.ForeignKey(
        'LegacyDiagnosisTranslation',
        on_delete=models.DO_NOTHING,
        db_column='DiagnosisTranslationSerNum',
    )
    description = models.CharField(db_column='Description', max_length=2056)
    diagnosis_code = models.CharField(db_column='DiagnosisCode', max_length=100)

    class Meta:
        managed = False
        db_table = 'DiagnosisCode'


class LegacyDiagnosis(models.Model):
    """Diagnosis from the legacy database OpalDB."""

    diagnosis_ser_num = models.AutoField(primary_key=True, db_column='DiagnosisSerNum')
    patient_ser_num = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    source_database = models.ForeignKey(
        LegacySourceDatabase,
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    diagnosis_aria_ser = models.CharField(db_column='DiagnosisAriaSer', max_length=32)
    diagnosis_code = models.CharField(db_column='DiagnosisCode', max_length=100)
    description_en = models.CharField(db_column='Description_EN', max_length=200)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    stage = models.CharField(db_column='Stage', max_length=32, blank=True, null=True)
    stage_criteria = models.CharField(db_column='StageCriteria', max_length=32, blank=True, null=True)
    creation_date = models.DateTimeField(db_column='CreationDate')

    objects: managers.LegacyDiagnosisManager = managers.LegacyDiagnosisManager()

    class Meta:
        managed = False
        db_table = 'Diagnosis'


class LegacyTestResult(models.Model):
    """TestResult from the legacy database OpalDB."""

    test_result_ser_num = models.AutoField(db_column='TestResultSerNum', primary_key=True)
    test_result_group_ser_num = models.IntegerField(db_column='TestResultGroupSerNum')
    test_result_control_ser_num = models.ForeignKey(
        'LegacyTestResultControl',
        models.DO_NOTHING,
        db_column='TestResultControlSerNum',
        to_field='test_result_control_ser_num',
    )
    test_result_expression_ser_num = models.IntegerField(db_column='TestResultExpressionSerNum')
    patient_ser_num = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    source_database = models.ForeignKey(
        LegacySourceDatabase,
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    test_result_aria_ser = models.CharField(db_column='TestResultAriaSer', max_length=100)
    component_name = models.CharField(db_column='ComponentName', max_length=30)
    fac_component_name = models.CharField(db_column='FacComponentName', max_length=30)
    abnormal_flag = models.CharField(db_column='AbnormalFlag', max_length=5)
    test_date = models.DateTimeField(db_column='TestDate')
    max_norm = models.FloatField(db_column='MaxNorm')
    min_norm = models.FloatField(db_column='MinNorm')
    approved_flag = models.CharField(db_column='ApprovedFlag', max_length=5)
    test_value = models.FloatField(db_column='TestValue')
    test_value_string = models.CharField(db_column='TestValueString', max_length=400)
    unit_description = models.CharField(db_column='UnitDescription', max_length=40)
    valid_entry = models.CharField(db_column='ValidEntry', max_length=5)
    date_added = models.DateTimeField(db_column='DateAdded')
    read_status = models.IntegerField(db_column='ReadStatus')
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'TestResult'


class LegacyTestResultControl(models.Model):
    """LegacyTestResultControl from the legacy database OpalDB."""

    test_result_control_ser_num = models.AutoField(primary_key=True, db_column='TestResultControlSerNum')
    name_en = models.CharField(max_length=200, db_column='Name_EN')
    name_fr = models.CharField(max_length=200, db_column='Name_FR')
    description_en = models.TextField(db_column='Description_EN')
    description_fr = models.TextField(db_column='Description_FR')
    group_en = models.CharField(max_length=200, db_column='Group_EN')
    group_fr = models.CharField(max_length=200, db_column='Group_FR')
    source_database = models.IntegerField(db_column='SourceDatabaseSerNum')
    publish_flag = models.IntegerField(db_column='PublishFlag')
    date_added = models.DateTimeField(db_column='DateAdded')
    last_published = models.DateTimeField(default='2002-01-01 00:00:00', db_column='LastPublished')
    last_updated_by = models.IntegerField(null=True, db_column='LastUpdatedBy')
    last_updated = models.DateTimeField(auto_now=True, db_column='LastUpdated')
    url_en = models.CharField(max_length=2000, db_column='URL_EN')
    url_fr = models.CharField(max_length=2000, db_column='URL_FR')

    class Meta:
        managed = False
        db_table = 'TestResultControl'


class LegacyPatientTestResult(models.Model):
    """PatientTestResult from the legacy database OpalDB."""

    patient_test_result_ser_num = models.AutoField(db_column='PatientTestResultSerNum', primary_key=True)
    test_group_expression_ser_num = models.ForeignKey(
        'LegacyTestGroupExpression',
        models.DO_NOTHING,
        db_column='TestGroupExpressionSerNum',
    )
    test_expression_ser_num = models.ForeignKey(
        'LegacyTestExpression',
        models.DO_NOTHING,
        db_column='TestExpressionSerNum',
    )
    patient_ser_num = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    abnormal_flag = models.CharField(db_column='AbnormalFlag', max_length=5)
    sequence_num = models.IntegerField(db_column='SequenceNum')
    collected_date_time = models.DateTimeField(db_column='CollectedDateTime')
    result_date_time = models.DateTimeField(db_column='ResultDateTime')
    normal_range_min = models.FloatField(db_column='NormalRangeMin')
    normal_range_max = models.FloatField(db_column='NormalRangeMax')
    normal_range = models.CharField(db_column='NormalRange', max_length=30)
    test_value_numeric = models.FloatField(db_column='TestValueNumeric')
    test_value_string = models.CharField(db_column='TestValue', max_length=255)
    unit_description = models.CharField(db_column='UnitDescription', max_length=40)
    date_added = models.DateTimeField(db_column='DateAdded', default=timezone.now)
    read_status = models.IntegerField(db_column='ReadStatus', default=0)
    read_by = models.TextField(db_column='ReadBy', blank=True)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    available_at = models.DateTimeField(db_column='AvailableAt', null=True)

    objects: managers.LegacyPatientTestResultManager = managers.LegacyPatientTestResultManager()

    class Meta:
        managed = False
        db_table = 'PatientTestResult'


class LegacyTestExpression(models.Model):
    """TestExpression from the legacy database OpalDB."""

    test_expression_ser_num = models.AutoField(db_column='TestExpressionSerNum', primary_key=True)
    test_control_ser_num = models.ForeignKey(
        'LegacyTestControl',
        models.DO_NOTHING,
        db_column='TestControlSerNum',
    )
    test_code = models.CharField(db_column='TestCode', max_length=30)
    expression_name = models.CharField(db_column='ExpressionName', max_length=100)
    date_added = models.DateTimeField(db_column='DateAdded', auto_now_add=True)
    last_published = models.DateTimeField(db_column='LastPublished', null=True, blank=True)
    last_updated_by = models.IntegerField(db_column='LastUpdatedBy', null=True, blank=True)
    source_database = models.ForeignKey(
        LegacySourceDatabase,
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    last_updated = models.DateTimeField(auto_now=True, db_column='LastUpdated')

    class Meta:
        managed = False
        db_table = 'TestExpression'


class LegacyTestGroupExpression(models.Model):
    """TestGroupExpression from the legacy database OpalDB."""

    test_group_expression_ser_num = models.AutoField(db_column='TestGroupExpressionSerNum', primary_key=True)
    test_code = models.CharField(db_column='TestCode', max_length=30)
    expression_name = models.CharField(db_column='ExpressionName', max_length=100)
    date_added = models.DateTimeField(db_column='DateAdded', auto_now_add=True)
    last_published = models.DateTimeField(db_column='LastPublished', null=True, blank=True)
    last_updated_by = models.IntegerField(db_column='LastUpdatedBy', null=True, blank=True)
    source_database = models.ForeignKey(
        LegacySourceDatabase,
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    last_updated = models.DateTimeField(auto_now=True, db_column='LastUpdated')

    class Meta:
        managed = False
        db_table = 'TestGroupExpression'


class LegacyTestControl(models.Model):
    """TextControl from the legacy database OpalDB."""

    test_control_ser_num = models.AutoField(db_column='TestControlSerNum', primary_key=True)
    name_en = models.CharField(db_column='Name_EN', max_length=200)
    name_fr = models.CharField(db_column='Name_FR', max_length=200)
    description_en = models.TextField(db_column='Description_EN')
    description_fr = models.TextField(db_column='Description_FR')
    group_en = models.CharField(db_column='Group_EN', max_length=200)
    group_fr = models.CharField(db_column='Group_FR', max_length=200)
    source_database = models.ForeignKey(
        LegacySourceDatabase,
        models.DO_NOTHING,
        db_column='SourceDatabaseSerNum',
        to_field='source_database',
    )
    educational_material_control_ser_num = models.ForeignKey(
        'LegacyEducationalMaterialControl',
        models.DO_NOTHING,
        db_column='EducationalMaterialControlSerNum',
    )
    publish_flag = models.IntegerField(db_column='PublishFlag')
    date_added = models.DateTimeField(db_column='DateAdded', auto_now_add=True)
    last_published = models.DateTimeField(db_column='LastPublished', null=True, blank=True)
    last_updated_by = models.IntegerField(db_column='LastUpdatedBy', null=True, blank=True)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    url_en = models.CharField(db_column='URL_EN', max_length=2000)
    url_fr = models.CharField(db_column='URL_FR', max_length=2000)

    class Meta:
        managed = False
        db_table = 'TestControl'


class LegacyOAUserType(models.IntegerChoices):
    """The user type for OA users."""

    HUMAN = 1
    SYSTEM = 2


class LegacyOAUser(models.Model):
    """OAUser from the legacy database OpalDB."""

    sernum = models.AutoField(db_column='OAUserSerNum', primary_key=True)
    username = models.CharField(db_column='Username', max_length=1000)
    password = models.CharField(db_column='Password', max_length=1000)
    oa_role = models.ForeignKey('LegacyOARole', models.DO_NOTHING, db_column='OaRoleId', default=1)
    user_type = models.IntegerField(db_column='type', choices=LegacyOAUserType.choices, default=LegacyOAUserType.HUMAN)
    language = models.CharField(db_column='Language', max_length=2, default='EN')
    is_deleted = models.IntegerField(db_column='deleted', default=0)
    date_added = models.DateTimeField(db_column='DateAdded', auto_now_add=True)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'OAUser'


class LegacyOARole(models.Model):
    """oaRole from the legacy database OpalDB."""

    role_id = models.AutoField(db_column='ID', primary_key=True)
    name_en = models.CharField(db_column='name_EN', max_length=64)
    name_fr = models.CharField(db_column='name_FR', max_length=64)
    is_deleted = models.IntegerField(db_column='deleted', default=0)
    deleted_by = models.CharField(db_column='deletedBy', max_length=255)
    creation_date = models.DateTimeField(db_column='creationDate', auto_now_add=True)
    created_by = models.CharField(db_column='createdBy', max_length=255)
    last_updated = models.DateTimeField(db_column='lastUpdated', auto_now=True)
    updated_by = models.CharField(db_column='updatedBy', max_length=255)

    class Meta:
        managed = False
        db_table = 'oaRole'


class LegacyOAUserRole(models.Model):
    """oaUserRole from the legacy database OpalDB."""

    oausersernum = models.IntegerField(db_column='OAUserSerNum')
    rolesernum = models.IntegerField(db_column='RoleSerNum')
    last_updated = models.DateTimeField(db_column='lastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'OAUserRole'


class LegacyModule(models.Model):
    """Module from the legacy database OpalDB."""

    moduleid = models.BigAutoField(db_column='ID', primary_key=True)
    operation = models.IntegerField(db_column='operation', default=7)
    name_en = models.CharField(db_column='name_EN', max_length=512)
    name_fr = models.CharField(db_column='name_FR', max_length=512)
    description_en = models.CharField(db_column='description_EN', max_length=512)
    description_fr = models.CharField(db_column='description_FR', max_length=512)
    tablename = models.CharField(db_column='tableName', max_length=256)
    controltablename = models.CharField(db_column='controlTableName', max_length=256)
    primarykey = models.CharField(db_column='primaryKey', max_length=256)
    iconclass = models.CharField(db_column='iconClass', max_length=512)
    url = models.CharField(db_column='url', max_length=255)
    sqlpublicationlist = models.TextField(db_column='sqlPublicationList')
    sqldetails = models.TextField(db_column='sqlDetails')
    sqlpublocationcharlog = models.TextField(db_column='sqlPublicationChartLog')
    sqlpublicationlistlog = models.TextField(db_column='sqlPublicationListLog')
    sqlpublicationmultiple = models.TextField(db_column='sqlPublicationMultiple')
    sqlpublicationunique = models.TextField(db_column='sqlPublicationUnique')

    class Meta:
        managed = False
        db_table = 'module'


class LegacyOARoleModule(models.Model):
    """oaRoleModule from the legacy database OpalDB."""

    rolemoduleid = models.BigAutoField(db_column='ID', primary_key=True)
    module = models.ForeignKey('LegacyModule', models.DO_NOTHING, db_column='moduleId')
    oa_role = models.ForeignKey('LegacyOARole', models.DO_NOTHING, db_column='OaRoleId')
    # Access level level (0-7) for this role on this module.
    access = models.IntegerField(db_column='access', default=0)

    class Meta:
        managed = False
        db_table = 'oaRoleModule'


class LegacyPatientActivityLog(models.Model):
    """PatientActivityLog from the legacy database OpalDB."""

    activity_ser_num = models.BigAutoField(db_column='ActivitySerNum', primary_key=True)
    request = models.CharField(db_column='Request', max_length=255, null=False)
    parameters = models.CharField(db_column='Parameters', max_length=2048, default='')
    target_patient_id = models.IntegerField(db_column='TargetPatientId', null=True)
    username = models.CharField(db_column='Username', max_length=255, null=False)
    device_id = models.CharField(db_column='DeviceId', max_length=255, null=False)
    session_id = models.TextField(db_column='SessionId', default='')
    date_time = models.DateTimeField(db_column='DateTime', null=False)
    lastupdated = models.DateTimeField(db_column='LastUpdated', null=False, default=timezone.now)
    app_version = models.CharField(db_column='AppVersion', max_length=50, null=False)

    objects: managers.LegacyPatientActivityLogManager = managers.LegacyPatientActivityLogManager()

    class Meta:
        managed = False
        db_table = 'PatientActivityLog'


class LegacyPatientDeviceIdentifier(models.Model):
    """PatientDeviceIdentifier from the legacy OpalDB database."""

    patient_device_identifier_ser_num = models.BigAutoField(db_column='PatientDeviceIdentifierSerNum', primary_key=True)
    device_id = models.CharField(db_column='DeviceId', max_length=255)
    app_version = models.CharField(db_column='appVersion', max_length=16)
    registration_id = models.CharField(db_column='RegistrationId', max_length=256)
    device_type = models.SmallIntegerField(db_column='DeviceType', default=0)  # 0 = iOS, 1 = Android, 3 = browser
    security_answer_ser_num = models.IntegerField(db_column='SecurityAnswerSerNum', null=True)
    attempt = models.IntegerField(db_column='Attempt', default=0)
    trusted = models.SmallIntegerField(db_column='Trusted', default=0)
    timeout_timestamp = models.DateTimeField(db_column='TimeoutTimestamp', null=True)
    last_updated = models.DateTimeField(db_column='LastUpdated', null=True, auto_now=True)
    username = models.CharField(db_column='Username', max_length=255, default='')
    security_answer = models.CharField(db_column='SecurityAnswer', max_length=256, default='')

    class Meta:
        managed = False
        db_table = 'PatientDeviceIdentifier'
