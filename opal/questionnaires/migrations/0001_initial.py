# Generated by Django 3.2.15 on 2022-09-22 15:25

from django.db import migrations, models


class Migration(migrations.Migration):
    """Report permission class which enables per-user access control for the questionnaire reporting tool."""

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExportReportPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Export Report',
                'verbose_name_plural': 'Export Reports',
                'permissions': (('export_report', 'Export Reports Permission'),),
                'managed': False,
                'default_permissions': (),
            },
        ),
    ]
