from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from opal.patients.models import RoleType
from opal.patients import constants


def set_can_answer_questionnaire(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Set correct defaults for `form_required` and `can_answer_questionnaire` fields to existing role types."""
    RelationshipType = apps.get_model('patients', 'RelationshipType')

    self_type = RelationshipType.objects.get(role_type=RoleType.SELF)
    self_type.can_answer_questionnaire = True
    self_type.form_required = False
    self_type.full_clean()
    self_type.save()

    guardian_type = RelationshipType.objects.get(role_type=RoleType.PARENT_GUARDIAN)
    guardian_type.can_answer_questionnaire = True
    guardian_type.full_clean()
    guardian_type.save()


def add_relationship_types(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Generate the restricted role type objects and save to database."""
    RelationshipType = apps.get_model('patients', 'RelationshipType')

    caregiver_type = RelationshipType.objects.filter(role_type=RoleType.GUARDIAN_CAREGIVER).first()

    if not caregiver_type:
        caregiver_type = RelationshipType.objects.filter(name='Guardian-Caregiver').first()

        if caregiver_type:
            caregiver_type.role_type = RoleType.GUARDIAN_CAREGIVER
            caregiver_type.full_clean()
            caregiver_type.save()
        else:
            RelationshipType.objects.create(
                name='Guardian-Caregiver',
                name_en='Guardian-Caregiver',
                name_fr='Gardien-Proche aidant',
                description='A parent or guardian of the patient',
                description_en='A parent or guardian of the patient',
                description_fr='Un parent ou un tuteur du patient',
                start_age=14,
                end_age=18,
                role_type=RoleType.GUARDIAN_CAREGIVER,
            )

    mandatary_type = RelationshipType.objects.filter(role_type=RoleType.MANDATARY).first()

    if not mandatary_type:
        mandatary_type = RelationshipType.objects.filter(name='Mandatary').first()

        if mandatary_type:
            mandatary_type.role_type = RoleType.MANDATARY
            mandatary_type.full_clean()
            mandatary_type.save()
        else:
            RelationshipType.objects.create(
                name='Mandatary',
                name_en='Mandatary',
                name_fr='Mandataire',
                description='Patient of any age legally under the care of the mandatary',
                description_en='Patient of any age legally under the care of the mandatary',
                description_fr='Patient de tout âge légalement sous la garde du mandataire',
                start_age=constants.RELATIONSHIP_MIN_AGE,
                role_type=RoleType.MANDATARY,
                can_answer_questionnaire=True,
            )


class Migration(migrations.Migration):
    """Populate the remaining missing relationship types, guardian-caregiver and mandatary."""

    dependencies = [
        ('patients', '0017_add_patient_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationshiptype',
            name='can_answer_questionnaire',
            field=models.BooleanField(default=False, help_text='The caregiver can answer questionnaires on behalf of the patient.', verbose_name='Can answer patient questionnaire'),
        ),
        migrations.AlterField(
            model_name='relationshiptype',
            name='role_type',
            field=models.CharField(
                choices=[
                    ('SELF', 'Self'),
                    ('PARENTGUARDIAN', 'Parent/Guardian'),
                    ('GRDNCAREGIVER', 'Guardian/Caregiver'),
                    ('MANDATARY', 'Mandatary'),
                    ('CAREGIVER', 'Caregiver'),
                ],
                default='CAREGIVER',
                help_text='Role types track the category of relationship between a caregiver and patient. A "Self" role type indicates a patient who owns the data that is being accessed.',
                max_length=14,
                verbose_name='Relationship Role Type',
            ),
        ),
        migrations.RunPython(set_can_answer_questionnaire, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(add_relationship_types, reverse_code=migrations.RunPython.noop),
    ]
