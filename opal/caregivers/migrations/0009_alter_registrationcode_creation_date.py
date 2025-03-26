# Generated by Django 4.1.7 on 2023-03-03 14:45

from django.db import migrations, models


class Migration(migrations.Migration):
    """Alter `creation_date` name to `created_at` and change its type to `DateTimeField`."""

    dependencies = [
        ('caregivers', '0008_modify_caregiverprofile_legacyid'),
    ]

    operations = [
        migrations.RenameField(
            model_name='registrationcode',
            old_name='creation_date',
            new_name='created_at',
        ),
        migrations.AlterField(
            model_name='registrationcode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
    ]
