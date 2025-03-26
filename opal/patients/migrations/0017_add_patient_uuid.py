import uuid

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def generate_uuid(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Generate a unique UUID for each patient."""
    Patient = apps.get_model('patients', 'Patient')

    for patient in Patient.objects.all():
        patient.uuid = uuid.uuid4()
        patient.save(update_fields=['uuid'])


class Migration(migrations.Migration):
    """Add a UUID field to the `Patient` model."""

    dependencies = [
        ('patients', '0016_add_manage_relationshiptype_permission'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, verbose_name='UUID'),
        ),
        migrations.RunPython(generate_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='patient',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
    ]
