from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    """Add two missing fields based on mockup: case_number (Report identifier) and reported_at (Additional timestamp)."""

    dependencies = [
        ('test_results', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='generaltest',
            name='case_number',
            field=models.CharField(blank=True, max_length=60, verbose_name='Filler Field 1'),
        ),
        migrations.AddField(
            model_name='generaltest',
            name='reported_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Reported At'),
            preserve_default=False,
        ),
    ]
