import uuid

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def generate_uuid(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Generate a unique UUID for each caregiver profile."""
    CaregiverProfile = apps.get_model('caregivers', 'CaregiverProfile')

    for caregiver in CaregiverProfile.objects.all():
        caregiver.uuid = uuid.uuid4()
        caregiver.save(update_fields=['uuid'])


class Migration(migrations.Migration):
    """Add uuid field to caregiver profile model."""

    dependencies = [
        ('caregivers', '0003_securityquestion'),
    ]

    operations = [
        migrations.AddField(
            model_name='caregiverprofile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True, verbose_name='UUID'),
        ),
        migrations.RunPython(generate_uuid, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='caregiverprofile',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID'),
        ),
    ]
