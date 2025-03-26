"""Module providing model factories for hospital settings app models."""
import factory
from factory.django import DjangoModelFactory

from . import models


class Institution(DjangoModelFactory):
    """Model factory to create [opal.hospital_settings.models.Institution][] models."""

    class Meta:
        model = models.Institution
        django_get_or_create = ('name',)

    name = 'McGill University Health Centre'
    name_fr = 'Centre universitaire de santé McGill'
    code = factory.lazy_attribute(lambda institution: institution.name[:4].upper())
    term_of_use = factory.django.FileField(data=b'test PDF', filename='test_term.pdf')


class Site(DjangoModelFactory):
    """Model factory to create [opal.hospital_settings.models.Site][] models."""

    class Meta:
        model = models.Site

    name = factory.Faker('company')
    name_fr = factory.Faker('company', locale='fr')
    code = factory.lazy_attribute(lambda site: site.name[:3].upper())
    parking_url = 'https://parking.example.com'
    parking_url_fr = 'https://parking.example.com/fr'
    direction_url = 'https://directions.example.com'
    direction_url_fr = 'https://directions.example.com/fr'
    institution = factory.SubFactory(Institution)
    # this is to create a float value with 16 digits decimal places.
    # function such as (lambda: ('%.16f' % 32))() can be used instead
    longitude = '43.3242143546534465'
    latitude = '32.3242143546534465'
