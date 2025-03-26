# Generated by Django 3.2.16 on 2022-12-02 15:18
from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from opal.patients.models import RoleType
from opal.patients import constants


def generate_restricted_roletypes(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Generate the restricted role type objects and save to database."""
    RelationshipType = apps.get_model('patients', 'RelationshipType')

    self_type = RelationshipType.objects.filter(role_type=RoleType.SELF).first()

    if not self_type:
        self_type = RelationshipType.objects.filter(name__iendswith='Self').first()

        if self_type:
            self_type.role_type = RoleType.SELF
            self_type.full_clean()
            self_type.save()
        else:
            RelationshipType.objects.create(
                name='Self',
                name_en='Self',
                name_fr='Soi',
                description='The patient is the requestor',
                description_en='The patient is the requestor',
                description_fr='Le patient est le demandeur',
                start_age=14,
                role_type=RoleType.SELF,
            )

    parent_type = RelationshipType.objects.filter(role_type=RoleType.PARENTGUARDIAN).first()

    if not parent_type:
        parent_type = RelationshipType.objects.filter(name__iendswith='guardian').first()

        if parent_type:
            parent_type.role_type = RoleType.PARENTGUARDIAN
            parent_type.full_clean()
            parent_type.save()
        else:
            RelationshipType.objects.create(
                name='Guardian',
                name_en='Guardian',
                name_fr='Gardien',
                description='A parent or guardian of the patient',
                description_en='A parent or guardian of the patient',
                description_fr='Un parent ou un tuteur du patient',
                start_age=constants.RELATIONSHIP_MIN_AGE,
                end_age=14,
                role_type=RoleType.PARENTGUARDIAN,
            )


class Migration(migrations.Migration):
    """Pre-populate deployment with the SELF and PARENTGUARDIAN role types."""

    dependencies = [
        ('patients', '0010_relationshiptype_role'),
    ]

    operations = [
        migrations.RunPython(generate_restricted_roletypes, reverse_code=migrations.RunPython.noop),
    ]
