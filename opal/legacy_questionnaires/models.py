"""
Module providing legacy models to provide access to the legacy QuestionnaireDB.

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


class LegacyDefinitionTable(models.Model):
    """DefinitionTable model from the legacy database QuestionnaireDB."""

    id = models.AutoField(db_column='ID', primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'definitionTable'


class LegacyDictionary(models.Model):
    """Dictionary model from the legacy database QuestionnaireDB.

    Note that contentId is NOT actually a unique field in QuestionnaireDB.
    Django forces us to add this constraint because contentId is referenced by many tables
    as a ForeignKey, and we cannot create a UniqueConstraint on this unmanaged model.
    This is okay as long as we only need to perform read operations on this table.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    table = models.ForeignKey(
        LegacyDefinitionTable,
        models.DO_NOTHING,
        db_column='tableId',
        to_field='id',
    )
    language_id = models.IntegerField(db_column='languageId')
    content_id = models.IntegerField(db_column='contentId', unique=True)
    content = models.CharField(db_column='content', max_length=255)
    deleted = models.SmallIntegerField(db_column='deleted', default=0)
    creation_date = models.DateTimeField(db_column='creationDate')
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')

    class Meta:
        managed = False
        db_table = 'dictionary'


class LegacyPurpose(models.Model):
    """Purpose model from the legacy database QuestionnaireDB.

    Dictionary is the 'endpoint' for defining queries in QuestionnaireDB as
    it just provides text for the integer identifiers in other tables.
    As such, we don't want Django to make a backwards relationship from Dictionary to Purpose,
    so set related_name attribute to '+' on ForeignKeys pointing to Dictionary.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='content_id',
        related_name='+',
    )

    class Meta:
        managed = False
        db_table = 'purpose'


class LegacyRespondent(models.Model):
    """Respondent model from the legacy database QuestionnaireDB."""

    id = models.AutoField(db_column='ID', primary_key=True)
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='content_id',
        related_name='+',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )

    class Meta:
        managed = False
        db_table = 'respondent'


class LegacyQuestionnaire(models.Model):
    """Questionnaire model from the legacy database QuestionnaireDB.

    This table records import metadata and identifiers for questionnaires.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    purpose = models.ForeignKey('LegacyPurpose', models.DO_NOTHING, db_column='purposeId', to_field='id')
    respondent = models.ForeignKey('LegacyRespondent', models.DO_NOTHING, db_column='respondentId', to_field='id')
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='content_id',
        related_name='+',
    )
    nickname = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='nickname',
        to_field='content_id',
        related_name='+',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    instruction = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='instruction',
        to_field='content_id',
        related_name='+',
    )
    logo = models.CharField(max_length=512)
    deleted_by = models.CharField(db_column='deletedBy', blank=True, max_length=255)
    creationdate = models.DateTimeField(db_column='creationDate')
    created_by = models.CharField(db_column='createdBy', max_length=255)
    updated_by = models.CharField(db_column='updatedBy', max_length=255)
    legacyname = models.CharField(db_column='legacyName', max_length=255)
    objects: managers.LegacyQuestionnaireManager = managers.LegacyQuestionnaireManager()

    class Meta:
        managed = False
        db_table = 'questionnaire'


class LegacyPatient(models.Model):
    """Patient model from the legacy database QuestionnaireDB.

    The patients in this table relate to OpalDB.Patient instances through the externalId.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    hospital_id = models.IntegerField(db_column='hospitalId')
    external_id = models.IntegerField(db_column='externalId')
    deleted = models.SmallIntegerField(db_column='deleted', default=0)
    creation_date = models.DateTimeField(db_column='creationDate')
    deleted_by = models.CharField(db_column='deletedBy', max_length=255)
    created_by = models.CharField(db_column='createdBy', max_length=255)
    updated_by = models.CharField(db_column='updatedBy', max_length=255)
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')

    class Meta:
        managed = False
        db_table = 'patient'


class LegacyAnswerQuestionnaire(models.Model):
    """Answer Questionnaire model from the legacy database QuestionnaireDB.

    This table records instances of a patient receiving a questionnaire
    and keeps track of the patient's progress on that questionnaire.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    questionnaire = models.ForeignKey(
        LegacyQuestionnaire,
        models.DO_NOTHING,
        db_column='questionnaireId',
        to_field='id',
    )
    patient = models.ForeignKey(
        LegacyPatient,
        models.DO_NOTHING,
        db_column='patientId',
        to_field='id',
    )
    status = models.IntegerField(db_column='status')
    creationdate = models.DateTimeField(db_column='creationDate')
    deleted_by = models.CharField(db_column='deletedBy', max_length=255)
    created_by = models.CharField(db_column='createdBy', max_length=255)
    updated_by = models.CharField(db_column='updatedBy', max_length=255)
    objects: managers.LegacyAnswerQuestionnaireManager = managers.LegacyAnswerQuestionnaireManager()

    class Meta:
        managed = False
        db_table = 'answerQuestionnaire'


class LegacyLanguage(models.Model):
    """Language model from the legacy database QuestionnaireDB."""

    iso_lang = models.CharField(max_length=2, db_column='isoLang')
    name = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='name',
        to_field='content_id',
        related_name='+',
    )
    deleted = models.BooleanField(default=False, db_column='deleted')
    deleted_by = models.CharField(max_length=255, default='', blank=True, db_column='deletedBy')
    creation_date = models.DateTimeField(auto_now_add=True, db_column='creationDate')
    created_by = models.CharField(max_length=255, db_column='createdBy')
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    updated_by = models.CharField(max_length=255, db_column='updatedBy')

    class Meta:
        db_table = 'language'
        managed = False


class LegacySection(models.Model):
    """Section model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    questionnaire = models.ForeignKey(
        'LegacyQuestionnaire',
        db_column='questionnaireId',
        on_delete=models.DO_NOTHING,
    )
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='content_id',
        related_name='+',
    )
    instruction = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='instruction',
        to_field='content_id',
        related_name='+',
    )
    order = models.IntegerField(default=1, db_column='order')
    deleted = models.BooleanField(default=False, db_column='deleted')
    deleted_by = models.CharField(max_length=255, default='', blank=True, db_column='deletedBy')
    creation_date = models.DateTimeField(db_column='creationDate')
    created_by = models.CharField(max_length=255, db_column='createdBy')
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    updated_by = models.CharField(max_length=255, db_column='updatedBy')

    class Meta:
        db_table = 'section'
        managed = False


class LegacyType(models.Model):
    """Type model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    table = models.ForeignKey('LegacyDefinitionTable', db_column='tableId', on_delete=models.DO_NOTHING)
    sub_table = models.ForeignKey(
        'LegacyDefinitionTable',
        db_column='subTableId',
        on_delete=models.DO_NOTHING,
        related_name='+',
    )
    template_table = models.ForeignKey(
        'LegacyDefinitionTable',
        db_column='templateTableId',
        on_delete=models.DO_NOTHING,
        related_name='+',
    )
    template_sub_table = models.ForeignKey(
        'LegacyDefinitionTable',
        db_column='templateSubTableId',
        on_delete=models.DO_NOTHING,
        related_name='+',
    )

    class Meta:
        db_table = 'type'
        managed = False


class LegacyQuestion(models.Model):
    """QuestionSection model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    display = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='display',
        to_field='content_id',
        related_name='+',
    )
    definition = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='definition',
        to_field='content_id',
        related_name='+',
    )
    question = models.BigIntegerField(db_column='question')
    type = models.ForeignKey(
        LegacyType,
        models.DO_NOTHING,
        db_column='typeId',
        to_field='id',
    )
    version = models.IntegerField(default=1, db_column='version')
    parent_id = models.BigIntegerField(default=-1, db_column='parentId')
    private = models.BooleanField(default=False, db_column='private')
    final = models.BooleanField(default=False, db_column='final')
    optional_feedback = models.BooleanField(default=False, db_column='optionalFeedback')
    deleted = models.BooleanField(default=False, db_column='deleted')
    deleted_by = models.CharField(max_length=255, default='', blank=True, db_column='deletedBy')
    creation_date = models.DateTimeField(db_column='creationDate')
    created_by = models.CharField(max_length=255, db_column='createdBy')
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    updated_by = models.CharField(max_length=255, db_column='updatedBy')
    legacy_type_id = models.BigIntegerField(default=1, db_column='legacyTypeId')

    class Meta:
        managed = False
        db_table = 'question'


class LegacyRadioButton(models.Model):
    """RadioButton model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    question = models.ForeignKey(
        LegacyQuestion,
        models.DO_NOTHING,
        db_column='questionId',
        to_field='id',
    )

    class Meta:
        db_table = 'radioButton'
        managed = False


class LegacyRadioButtonOption(models.Model):
    """RadioButtonOption model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    parent_table = models.ForeignKey(
        LegacyRadioButton,
        models.DO_NOTHING,
        db_column='parentTableId',
        to_field='id',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    order = models.IntegerField(default=1)

    class Meta:
        db_table = 'radioButtonOption'
        managed = False


class LegacyCheckbox(models.Model):
    """Checkbox model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    question = models.ForeignKey(
        LegacyQuestion,
        models.DO_NOTHING,
        db_column='questionId',
        to_field='id',
    )

    class Meta:
        db_table = 'checkbox'
        managed = False


class LegacyCheckboxOption(models.Model):
    """CheckboxOption model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    order = models.IntegerField(default=1, db_column='order')
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    parent_table = models.ForeignKey(
        LegacyCheckbox,
        models.DO_NOTHING,
        db_column='parentTableId',
        to_field='id',
    )

    class Meta:
        db_table = 'checkboxOption'
        managed = False


class LegacyLabel(models.Model):
    """Label model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    question = models.ForeignKey(
        LegacyQuestion,
        models.DO_NOTHING,
        db_column='questionId',
        to_field='id',
    )

    class Meta:
        db_table = 'label'
        managed = False


class LegacyLabelOption(models.Model):
    """LabelOption model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    parent_table = models.ForeignKey(
        LegacyLabel,
        models.DO_NOTHING,
        db_column='parentTableId',
        to_field='id',
        related_name='+',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='content_id',
        related_name='+',
    )
    pos_init_x = models.IntegerField(default=0, db_column='posInitX')
    pos_init_y = models.IntegerField(default=0, db_column='posInitY')
    pos_final_x = models.IntegerField(default=0, db_column='posFinalX')
    pos_final_y = models.IntegerField(default=0, db_column='posFinalY')
    intensity = models.IntegerField(default=0, db_column='intensity')
    order = models.IntegerField(default=1, db_column='order')

    class Meta:
        db_table = 'labelOption'
        managed = False


class LegacyQuestionSection(models.Model):
    """QuestionSection model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    question = models.ForeignKey(
        LegacyQuestion,
        models.DO_NOTHING,
        db_column='questionId',
        to_field='id',
    )
    section = models.ForeignKey(
        LegacySection,
        models.DO_NOTHING,
        db_column='sectionId',
        to_field='id',
    )
    order = models.IntegerField(db_column='order', default=1)
    orientation = models.IntegerField(db_column='orientation', default=0)
    optional = models.BooleanField(db_column='optional', default=False)

    class Meta:
        db_table = 'questionSection'
        managed = False


class LegacyAnswerSection(models.Model):
    """AnswerSection model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer_questionnaire = models.ForeignKey(
        LegacyAnswerQuestionnaire,
        models.DO_NOTHING,
        db_column='answerQuestionnaireId',
        to_field='id',
    )
    section = models.ForeignKey(
        LegacySection,
        models.DO_NOTHING,
        db_column='sectionId',
        to_field='id',
    )

    class Meta:
        managed = False
        db_table = 'answerSection'


class LegacyAnswer(models.Model):
    """Answer model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    questionnaire = models.ForeignKey(
        LegacyQuestionnaire,
        models.DO_NOTHING,
        db_column='questionnaireId',
        to_field='id',
    )
    section = models.ForeignKey(
        LegacySection,
        models.DO_NOTHING,
        db_column='sectionId',
        to_field='id',
    )
    question = models.ForeignKey(
        LegacyQuestion,
        models.DO_NOTHING,
        db_column='questionId',
        to_field='id',
    )
    type = models.ForeignKey(
        LegacyType,
        models.DO_NOTHING,
        db_column='typeId',
        to_field='id',
    )
    answer_section = models.ForeignKey(
        LegacyAnswerSection,
        models.DO_NOTHING,
        db_column='answerSectionId',
        to_field='id',
    )
    language = models.ForeignKey(
        LegacyLanguage,
        models.DO_NOTHING,
        db_column='languageId',
        to_field='id',
    )
    patient = models.ForeignKey(
        LegacyPatient,
        models.DO_NOTHING,
        db_column='patientId',
        to_field='id',
    )
    answered = models.BooleanField(default=False, db_column='answered')
    skipped = models.BooleanField(default=False, db_column='skipped')
    deleted = models.BooleanField(default=False, db_column='deleted')
    deleted_by = models.CharField(max_length=255, default='', db_column='deletedBy')
    creation_date = models.DateTimeField(db_column='creationDate')
    created_by = models.CharField(max_length=255, db_column='createdBy')
    last_updated = models.DateTimeField(auto_now=True, db_column='lastUpdated')
    updated_by = models.CharField(max_length=255, db_column='updatedBy')

    class Meta:
        managed = False
        db_table = 'answer'


class LegacyAnswerSlider(models.Model):
    """AnswerSlider model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.FloatField()

    class Meta:
        managed = False
        db_table = 'answerSlider'


class LegacyAnswerTextBox(models.Model):
    """AnswerTextBox model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.TextField()

    class Meta:
        managed = False
        db_table = 'answerTextBox'


class LegacyAnswerTime(models.Model):
    """AnswerTime model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.TimeField()

    class Meta:
        managed = False
        db_table = 'answerTime'


class LegacyAnswerLabel(models.Model):
    """AnswerLabel model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    selected = models.SmallIntegerField(default=1, db_column='selected')
    pos_x = models.IntegerField(db_column='posX')
    pos_y = models.IntegerField(db_column='posY')
    intensity = models.IntegerField(db_column='intensity')
    value = models.BigIntegerField(db_column='value')

    class Meta:
        managed = False
        db_table = 'answerLabel'


class LegacyAnswerRadioButton(models.Model):
    """AnswerRadioButton model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.BigIntegerField(db_column='value')

    class Meta:
        managed = False
        db_table = 'answerRadioButton'


class LegacyAnswerCheckbox(models.Model):
    """AnswerCheckbox model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.BigIntegerField(db_column='value')

    class Meta:
        managed = False
        db_table = 'answerCheckbox'


class LegacyAnswerDate(models.Model):
    """AnswerDate model from the legacy database QuestionnaireDB."""

    id = models.BigAutoField(primary_key=True, db_column='ID')
    answer = models.ForeignKey(
        LegacyAnswer,
        models.DO_NOTHING,
        db_column='answerId',
        to_field='id',
    )
    value = models.DateTimeField(db_column='value')

    class Meta:
        managed = False
        db_table = 'answerDate'
