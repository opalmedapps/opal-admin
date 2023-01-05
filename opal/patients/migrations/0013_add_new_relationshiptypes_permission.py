# Generated by Django 3.2.16 on 2023-01-05 15:10

from django.db import migrations


class Migration(migrations.Migration):
    """Add `can_manage_relationshiptypes` permission to Patient model."""

    dependencies = [
        ('patients', '0012_add_manage_relationship_permission'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='relationshiptype',
            options={'ordering': ['name'], 'permissions': (('can_manage_relationshiptypes', 'Can manage relationshiptypes'),), 'verbose_name': 'Caregiver Relationship Type', 'verbose_name_plural': 'Caregiver Relationship Types'},
        ),
    ]
