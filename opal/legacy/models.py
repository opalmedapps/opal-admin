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

    class Meta:
        managed = False
        db_table = 'Patient'


class LegacyNotification(models.Model):
    """Notification model from the legacy database OpalDB."""

    notificationsernum = models.AutoField(db_column='NotificationSerNum', primary_key=True)
    patientsernum = models.ForeignKey('LegacyPatient', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')

    class Meta:
        managed = False
        db_table = 'Notification'


class LegacyAppointment(models.Model):
    """Class to get appointement informations from the legacy database."""

    appointmentsernum = models.AutoField(db_column='AppointmentSerNum', primary_key=True)
    aliasexpressionsernum = models.ForeignKey(
        'LegacyAliasexpression',
        models.DO_NOTHING,
        db_column='AliasExpressionSerNum',
    )
    patientsernum = models.ForeignKey(
        'LegacyPatient',
        models.DO_NOTHING,
        db_column='PatientSerNum',
    )
    state = models.CharField(db_column='State', max_length=25)
    scheduledstarttime = models.DateTimeField(db_column='ScheduledStartTime')
    checkin = models.IntegerField(db_column='Checkin')
    status = models.CharField(db_column='Status', max_length=100)

    class Meta:
        managed = False
        db_table = 'Appointment'


class LegacyAliasexpression(models.Model):
    """Legcy alias expression model mapping AliasExpression table from legacy database."""

    aliasexpressionsernum = models.AutoField(db_column='AliasExpressionSerNum', primary_key=True)
    aliassernum = models.ForeignKey('LegacyAlias', models.DO_NOTHING, db_column='AliasSerNum')

    class Meta:
        managed = False
        db_table = 'AliasExpression'


class LegacyAlias(models.Model):
    """Legacy alias model mapping Alias table from legacy database."""

    aliassernum = models.AutoField(db_column='AliasSerNum', primary_key=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Alias'


class LegacyAppointmentcheckin(models.Model):
    """Legacy appointment checkin mapping appointmentcheckin table from the legacu database."""

    aliassernum = models.OneToOneField(
        'LegacyAlias',
        models.DO_NOTHING,
        db_column='AliasSerNum',
        primary_key=True,
        related_name='appointmentcheckin',
    )
    checkinpossible = models.IntegerField(db_column='CheckinPossible')

    class Meta:
        managed = False
        db_table = 'AppointmentCheckin'
