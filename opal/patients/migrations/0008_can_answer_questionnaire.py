# Generated by Django 3.2.16 on 2022-11-17 01:01

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add `can_answer_questionnaire` field to RelationshipType model."""

    dependencies = [
        ('patients', '0007_patient_hin_to_ramq'),
    ]

    operations = [
        migrations.AddField(
            model_name='relationshiptype',
            name='can_answer_questionnaire',
            field=models.BooleanField(default=False, help_text='The caregiver can answer questionnaires on behalf of the patient.', verbose_name='Right to answer questionnaire'),
        ),
    ]
