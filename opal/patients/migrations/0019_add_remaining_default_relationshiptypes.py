from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from opal.patients.models import RoleType
from opal.patients import constants


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
                description='A parent or guardian of a minor who is considered incapacitated in terms of self-care',
                description_en='A parent or guardian of a minor who is considered incapacitated in terms of self-care',
                description_fr="Un parent ou un tuteur d'un mineur qui est considéré comme incapable de prendre soin de lui-même",
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
                description='A mandatary legally caring for a patient of any age',
                description_en='A mandatary legally caring for a patient of any age',
                description_fr="Un mandataire qui prend soin légalement d'un patient de tout âge",
                start_age=constants.RELATIONSHIP_MIN_AGE,
                role_type=RoleType.MANDATARY,
                can_answer_questionnaire=True,
            )


class Migration(migrations.Migration):
    """Populate the remaining missing relationship types, guardian-caregiver and mandatary."""

    dependencies = [
        ('patients', '0018_update_existing_relationshiptypes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationshiptype',
            name='role_type',
            field=models.CharField(
                choices=[
                    ('SELF', 'Self'),
                    ('PARENTGUARDIAN', 'Parent/Guardian'),
                    ('GRDNCAREGIVER', 'Guardian-Caregiver'),
                    ('MANDATARY', 'Mandatary'),
                    ('CAREGIVER', 'Caregiver'),
                ],
                default='CAREGIVER',
                help_text='Role types track the category of relationship between a caregiver and patient. A "Self" role type indicates a patient who owns the data that is being accessed.',
                max_length=14,
                verbose_name='Relationship Role Type',
            ),
        ),
        migrations.RunPython(add_relationship_types, reverse_code=migrations.RunPython.noop),
    ]
