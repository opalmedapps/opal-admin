# Generated by Django 3.2.13 on 2022-07-01 19:40

from django.db import migrations, models


class Migration(migrations.Migration):
    """Change the language field to use the project's settings."""

    dependencies = [
        ('users', '0004_user_phone_number'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='user',
            name='users_user_language_valid',
        ),
        migrations.AlterField(
            model_name='user',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('fr', 'French')], default='en', max_length=2, verbose_name='Language'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(('language__in', ['en', 'fr'])), name='users_user_language_valid'),
        ),
    ]
