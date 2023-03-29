from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from opal.patients.models import RoleType


def update_data(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """
    Set correct defaults for `form_required` and `can_answer_questionnaire` fields to existing role types.

    Fix the name of the parent/guardian relationship type.

    See migration 0014 for the initial data.
    """
    RelationshipType = apps.get_model('patients', 'RelationshipType')

    self_type = RelationshipType.objects.get(role_type=RoleType.SELF)
    self_type.description = 'The patient is the requestor and is caring for themselves'
    self_type.description_en = self_type.description
    self_type.description_fr = 'Le patient est le demandeur et prend soin de lui-même'
    self_type.can_answer_questionnaire = True
    self_type.form_required = False
    self_type.full_clean()
    self_type.save()

    guardian_type = RelationshipType.objects.get(role_type=RoleType.PARENT_GUARDIAN)
    guardian_type.name = 'Parent/Guardian'
    guardian_type.name_en = guardian_type.name
    guardian_type.name_fr = 'Parent/Tuteur'
    guardian_type.description = 'Parent or guardian of a minor under the age of medical consent legally under their care'
    guardian_type.description_en = guardian_type.description
    guardian_type.description_fr = "Parent ou tuteur d'un mineur sous l'âge de consentement médical, légalement sous sa garde"
    guardian_type.can_answer_questionnaire = True
    guardian_type.full_clean()
    guardian_type.save()


class Migration(migrations.Migration):
    """Fix the data of the existing predefined relationship types."""

    dependencies = [
        ('patients', '0017_add_patient_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relationshiptype',
            name='can_answer_questionnaire',
            field=models.BooleanField(default=False, help_text='The caregiver can answer questionnaires on behalf of the patient.', verbose_name='Can answer patient questionnaires'),
        ),
        migrations.RunPython(update_data, reverse_code=migrations.RunPython.noop),
    ]
