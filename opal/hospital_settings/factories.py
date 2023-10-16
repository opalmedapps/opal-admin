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
    logo = factory.django.ImageField(from_path='opal/tests/fixtures/test_logo.png')
    logo_fr = factory.django.ImageField(from_path='opal/tests/fixtures/test_logo.png')
    code = factory.lazy_attribute(lambda institution: institution.name[:4].upper())
    terms_of_use = factory.django.FileField(data=b'test PDF', filename='test_terms.pdf')
    terms_of_use_fr = factory.django.FileField(data=b'PDF pour tester', filename='test_terms.pdf')
    support_email = 'muhc@muhc.mcgill.ca'
    adulthood_age = 18
    non_interpretable_lab_result_delay = 0
    interpretable_lab_result_delay = 0
    registration_code_valid_period = 72


class Site(DjangoModelFactory):
    """Model factory to create [opal.hospital_settings.models.Site][] models."""

    class Meta:
        model = models.Site

    name = factory.Faker('company')
    name_fr = factory.Faker('company', locale='fr')
    code = factory.lazy_attribute(
        # ensure that spaces in the name don't get used as part of the code
        # spaces are truncated leading to a code with a smaller length
        lambda site: site.name.replace(' ', 'x')[:4].upper(),
    )
    parking_url = 'https://parking.example.com'
    parking_url_fr = 'https://parking.example.com/fr'
    direction_url = 'https://directions.example.com'
    direction_url_fr = 'https://directions.example.com/fr'
    institution = factory.SubFactory(Institution)
    # this is to create a float value with 16 digits decimal places.
    # function such as (lambda: ('%.16f' % 32))() can be used instead
    longitude = '43.3242143546534465'
    latitude = '32.3242143546534465'
    street_name = 'TEST Boulevard'
    street_number = '0001'
    postal_code = 'A1A9Z9'
    city = 'Montreal'
    province_code = 'QC'
    contact_telephone = '5149341934'
    contact_fax = '5149341934'
