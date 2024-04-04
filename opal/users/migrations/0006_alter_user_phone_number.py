from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):
    """Change phone number field to use `PhoneNumberField`."""

    dependencies = [
        ('users', '0005_user_language_settings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=128, region=None, verbose_name='Phone Number',
            ),
        ),
    ]
