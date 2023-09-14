from django.db import migrations, models


class Migration(migrations.Migration):
    """Make the Observation.value field free form text for allow for large pathology reports."""

    dependencies = [
        ('test_results', '0003_use_plural_form_for_related_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='value',
            field=models.TextField(verbose_name='Value'),
        ),
    ]
