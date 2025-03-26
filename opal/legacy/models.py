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

from django.db import models

from . import managers


class LegacyUsers(models.Model):
    """User model from the legacy database OpalDB."""

    usersernum = models.AutoField(db_column='UserSerNum', primary_key=True)
    usertype = models.CharField(db_column='UserType', max_length=255)
    usertypesernum = models.IntegerField(db_column='UserTypeSerNum')
    username = models.CharField(db_column='Username', max_length=255)

    class Meta:
        managed = False
        db_table = 'Users'


class LegacyPatient(models.Model):
    """Patient model from the legacy database."""

    patientsernum = models.AutoField(db_column='PatientSerNum', primary_key=True)
    firstname = models.CharField(db_column='FirstName', max_length=50)
    lastname = models.CharField(db_column='LastName', max_length=50)
    email = models.CharField(db_column='Email', max_length=50)
    registrationdate = models.DateTimeField(db_column='RegistrationDate')
    language = models.CharField(db_column='Language', max_length=2)
    telnum = models.BigIntegerField(db_column='TelNum', blank=True, null=True)
    dateofbirth = models.DateTimeField(db_column='DateOfBirth')
    death_date = models.DateTimeField(db_column='DeathDate', blank=True, null=True)
    ssn = models.CharField(db_column='SSN', max_length=16)
    accesslevel = models.CharField(db_column='AccessLevel', max_length=1, default='1')
    sex = models.CharField(db_column='Sex', max_length=25)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    patient_aria_ser = models.IntegerField(db_column='PatientAriaSer')

    objects: managers.LegacyPatientManager = managers.LegacyPatientManager()

    class Meta:
        managed = False
        db_table = 'Patient'


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
    """Class to get appointement informations from the legacy database."""

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
    appointment_aria_ser = models.IntegerField(db_column='AppointmentAriaSer')
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
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')
    readby = models.JSONField(db_column='ReadBy', default=list)
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
    objects: managers.LegacyEducationalMaterialManager = managers.LegacyEducationalMaterialManager()

    class Meta:
        managed = False
        db_table = 'EducationalMaterial'


class LegacyEducationalMaterialControl(models.Model):
    """EducationalMaterialControl model from the legacy database OpalDB."""

    educationalmaterialcontrolsernum = models.AutoField(db_column='EducationalMaterialControlSerNum', primary_key=True)
    educationalmaterialcategoryid = models.ForeignKey(
        'LegacyEducationalMaterialCategory',
        models.DO_NOTHING,
        db_column='EducationalMaterialCategoryId',
    )

    class Meta:
        managed = False
        db_table = 'EducationalMaterialControl'


class LegacyEducationalMaterialCategory(models.Model):
    """EducationalMaterialCategory model from the legacy database OpalDB."""

    id = models.AutoField(db_column='ID', primary_key=True)  # noqa: A003
    title_en = models.CharField(db_column='title_EN', max_length=128)
    title_fr = models.CharField(db_column='title_FR', max_length=128)

    class Meta:
        managed = False
        db_table = 'EducationalMaterialCategory'


class LegacyQuestionnaire(models.Model):
    """Questionnaire model from the legacy database OpalDB."""

    questionnairesernum = models.BigAutoField(db_column='QuestionnaireSerNum', primary_key=True)
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    completedflag = models.IntegerField(db_column='CompletedFlag')
    objects: managers.LegacyQuestionnaireManager = managers.LegacyQuestionnaireManager()

    class Meta:
        managed = False
        db_table = 'Questionnaire'


class LegacyAnnouncement(models.Model):
    """Announcement model from the legacy database OpalDB."""

    announcementsernum = models.AutoField(db_column='AnnouncementSerNum', primary_key=True)
    postcontrolsernum = models.ForeignKey('LegacyPostcontrol', models.DO_NOTHING, db_column='PostControlSerNum')
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
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    answertext = models.CharField(db_column='AnswerText', max_length=2056)
    creationdate = models.DateTimeField(db_column='CreationDate')
    lastupdated = models.DateTimeField(db_column='LastUpdated', auto_now=True)

    class Meta:
        managed = False
        db_table = 'SecurityAnswer'
        unique_together = (('securityquestionsernum', 'patientsernum'),)


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
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    hospitalidentifiertypecode = models.ForeignKey(
        'LegacyHospitalIdentifierType',
        models.DO_NOTHING,
        db_column='Hospital_Identifier_Type_Code',
        to_field='code',
    )
    mrn = models.CharField(db_column='MRN', max_length=20)
    isactive = models.BooleanField(db_column='is_Active')

    class Meta:
        managed = False
        db_table = 'Patient_Hospital_Identifier'
        unique_together = (('patientsernum', 'hospitalidentifiertypecode', 'mrn'),)


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

    id = models.AutoField(primary_key=True, db_column='ID')  # noqa: A003
    external_id = models.CharField(db_column='externalId', max_length=512)
    code = models.CharField(db_column='code', max_length=128)
    description = models.CharField(db_column='description', max_length=128)

    class Meta:
        managed = False
        db_table = 'masterSourceAlias'


class LegacyDiagnosis(models.Model):
    """Diagnosis from the legacy database OpalDB."""

    diagnosis_ser_num = models.AutoField(primary_key=True, db_column='DiagnosisSerNum')
    patient_ser_num = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    source_database = models.IntegerField(db_column='SourceDatabaseSerNum')
    diagnosis_aria_ser = models.CharField(db_column='DiagnosisAriaSer', max_length=32)
    diagnosis_code = models.CharField(db_column='DiagnosisCode', max_length=50)
    last_updated = models.DateTimeField(db_column='LastUpdated', auto_now=True)
    stage = models.CharField(db_column='Stage', max_length=32, blank=True, null=True)  # noqa: DJ01
    stage_criteria = models.CharField(db_column='StageCriteria', max_length=32, blank=True, null=True)  # noqa: DJ01
    creation_date = models.DateTimeField(db_column='CreationDate')

    class Meta:
        managed = False
        db_table = 'Diagnosis'


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


class LegacyTestResult(models.Model):
    """TestResult from the legacy database OpalDB."""

    test_result_ser_num = models.AutoField(db_column='TestResultSerNum', primary_key=True)
    test_result_group_ser_num = models.IntegerField(db_column='TestResultGroupSerNum')
    test_result_control_ser_num = models.IntegerField(db_column='TestResultControlSerNum')
    test_result_expression_ser_num = models.IntegerField(db_column='TestResultExpressionSerNum')
    patient_ser_num = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    source_database = models.IntegerField(db_column='SourceDatabaseSerNum')
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
