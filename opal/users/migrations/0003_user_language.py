# Generated by Django 4.0.3 on 2022-04-28 13:17

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add a language field to the user model."""

    dependencies = [
        ('users', '0002_add_user_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(choices=[('EN', 'English'), ('FR', 'French')], default='FR', max_length=2, verbose_name='Language'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(('language__in', ['EN', 'FR'])), name='users_user_language_valid'),
        ),
    ]
