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
    usertypesernum = models.IntegerField(db_column='UserTypeSerNum')
    username = models.CharField(db_column='Username', max_length=255)

    class Meta:
        managed = False
        db_table = 'Users'


class LegacyNotification(models.Model):
    """Notification model from the legacy database OpalDB."""

    notificationsernum = models.AutoField(db_column='NotificationSerNum', primary_key=True)
    patientsernum = models.ForeignKey('LegacyUsers', models.DO_NOTHING, db_column='PatientSerNum')
    readstatus = models.IntegerField(db_column='ReadStatus')

    class Meta:
        managed = False
        db_table = 'Notification'


class LegacyAppointment(models.Model):
    """Class to get appintement informations from the legacy database."""

    appointmentsernum = models.AutoField(db_column='AppointmentSerNum', primary_key=True)
    patientsernum = models.ForeignKey(
        'LegacyUsers',
        models.DO_NOTHING,
        db_column='PatientSerNum',
    )
    status = models.CharField(db_column='Status', max_length=100)
    state = models.CharField(db_column='State', max_length=25)
    scheduledstarttime = models.DateTimeField(db_column='ScheduledStartTime')
    location = models.IntegerField(db_column='Location')
    roomlocation_en = models.CharField(db_column='RoomLocation_EN', max_length=100)
    roomlocation_fr = models.CharField(db_column='RoomLocation_FR', max_length=100)
    checkin = models.IntegerField(db_column='Checkin')

    class Meta:
        managed = False
        db_table = 'Appointment'
