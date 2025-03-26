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
    tableid = models.ForeignKey(
        LegacyDefinitionTable,
        models.DO_NOTHING,
        db_column='tableId',
        to_field='id',
    )
    languageid = models.IntegerField(db_column='languageId')
    contentid = models.IntegerField(db_column='contentId', unique=True)
    content = models.CharField(db_column='content', max_length=255)
    deleted = models.SmallIntegerField(db_column='deleted', default=0)
    creationdate = models.DateTimeField(db_column='creationDate')

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
        to_field='contentid',
        related_name='+',
    )
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='contentid',
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
        to_field='contentid',
        related_name='+',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='contentid',
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
    purposeid = models.ForeignKey('LegacyPurpose', models.DO_NOTHING, db_column='purposeId', to_field='id')
    respondentid = models.ForeignKey('LegacyRespondent', models.DO_NOTHING, db_column='respondentId', to_field='id')
    title = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='title',
        to_field='contentid',
        related_name='+',
    )
    nickname = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='nickname',
        to_field='contentid',
        related_name='+',
    )
    description = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='description',
        to_field='contentid',
        related_name='+',
    )
    instruction = models.ForeignKey(
        LegacyDictionary,
        models.DO_NOTHING,
        db_column='instruction',
        to_field='contentid',
        related_name='+',
    )
    logo = models.CharField(max_length=512)
    deletedby = models.CharField(db_column='deletedBy', max_length=255)
    creationdate = models.DateTimeField(db_column='creationDate')
    createdby = models.CharField(db_column='createdBy', max_length=255)
    updatedby = models.CharField(db_column='updatedBy', max_length=255)
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
    hospitalid = models.IntegerField(db_column='hospitalId')
    externalid = models.IntegerField(db_column='externalId')
    deleted = models.SmallIntegerField(db_column='deleted', default=0)
    creationdate = models.DateTimeField(db_column='creationDate')
    deletedby = models.CharField(db_column='deletedBy', max_length=255)
    createdby = models.CharField(db_column='createdBy', max_length=255)
    updatedby = models.CharField(db_column='updatedBy', max_length=255)

    class Meta:
        managed = False
        db_table = 'patient'


class LegacyAnswerQuestionnaire(models.Model):
    """Answer Questionnaire model from the legacy database QuestionnaireDB.

    This table records instances of a patient receiving a questionnaire
    and keeps track of the patient's progress on that questionnaire.
    """

    id = models.AutoField(db_column='ID', primary_key=True)
    questionnaireid = models.ForeignKey(
        LegacyQuestionnaire,
        models.DO_NOTHING,
        db_column='questionnaireId',
        to_field='id',
    )
    patientid = models.ForeignKey(
        LegacyPatient,
        models.DO_NOTHING,
        db_column='patientId',
        to_field='id',
    )
    status = models.IntegerField(db_column='status')
    creationdate = models.DateTimeField(db_column='creationDate')
    deletedby = models.CharField(db_column='deletedBy', max_length=255)
    createdby = models.CharField(db_column='createdBy', max_length=255)
    updatedby = models.CharField(db_column='updatedBy', max_length=255)

    class Meta:
        managed = False
        db_table = 'answerQuestionnaire'
