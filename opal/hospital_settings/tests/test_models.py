from django.core.exceptions import ValidationError
from django.db import IntegrityError, models

import pytest
from pytest_django.asserts import assertRaisesMessage

from .. import constants, factories
from ..models import Institution, RelationshipType, Site

TEST_HOSPITAL = 'Test Hospital'

pytestmark = pytest.mark.django_db


# INSTITUTION TESTS

# Test Institution.name field

def test_institution_name_label() -> None:
    """Check that the `name` field label (`verbose_name`) is as expected."""
    assert Institution._meta.get_field('name').verbose_name == 'Name'


def test_institution_name_max_length() -> None:
    """Check that the max size of the `name` field is as expected."""
    assert Institution._meta.get_field('name').max_length == 100


# TODO: Check that the min size of the `name` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_institution_name_blank() -> None:
    """Check that the `name` field cannot be blank (doesn't accept an empty string)."""
    assert not Institution._meta.get_field('name').blank


def test_institution_name_null() -> None:
    """Check that the `name` field cannot be NULL (doesn't accept `None`)."""
    # Note that `django-modeltranslation` makes the `name_fr` and `name_en` fields Nullable (`null=True`).
    # See the doc: https://django-modeltranslation.readthedocs.io/en/latest/registration.html#required-fields
    assert not Institution._meta.get_field('name').null


def test_institution_name_type() -> None:
    """Check that the `name` field type is `models.CharField`."""
    assert Institution._meta.get_field('name').__class__ == models.CharField


# Test Institution.code field

def test_institution_code_label() -> None:
    """Check that the `code` field label (`verbose_name`) is as expected."""
    assert Institution._meta.get_field('code').verbose_name == 'Code'


def test_institution_code_max_length() -> None:
    """Check that the size of the `code` field is as expected."""
    assert Institution._meta.get_field('code').max_length == 10


# TODO: Check that the min size of the `code` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_institution_code_blank() -> None:
    """Check that the `code` field cannot be blank (doesn't accept an empty string)."""
    assert not Institution._meta.get_field('code').blank


def test_institution_code_null() -> None:
    """Check that the `code` field cannot be NULL (doesn't accept `None`)."""
    assert not Institution._meta.get_field('code').null


def test_institution_code_type() -> None:
    """Check that the `code` field type is `models.CharField`."""
    assert Institution._meta.get_field('code').__class__ == models.CharField


def test_institution_code_unique() -> None:
    """Check that the `code` field is unique."""
    assert Institution._meta.get_field('code').unique  # type: ignore


# Test Institution verbose names

def test_institution_verbose_name() -> None:
    """Check that `Institution` verbose name is as expected."""
    assert Institution._meta.verbose_name == 'Institution'


def test_institution_verbose_name_plural() -> None:
    """Check that `Institution` verbose plural name is as expected."""
    assert Institution._meta.verbose_name_plural == 'Institutions'


# Test Institution string method

def test_institution_string_method() -> None:
    """Ensure that the `__str__` method is defined for the `Institution` model."""
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name=TEST_HOSPITAL, code='TH')
    assert str(institution) == TEST_HOSPITAL


# Test Institution ordering

def test_institution_ordered() -> None:
    """Ensure that the institutions are ordered by name."""
    Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Institution.objects.create(name='ATest Hospital', code='TH2')
    first = Institution.objects.all()[0]
    assert first.name == 'ATest Hospital'


# Site tests

# Test Site.name field

def test_site_name_label() -> None:
    """Check that the `name` field label (`verbose_name`) is as expected."""
    assert Site._meta.get_field('name').verbose_name == 'Name'


def test_site_name_max_length() -> None:
    """Check that the size of the `name` field is as expected."""
    assert Site._meta.get_field('name').max_length == 100


# TODO: Check that the min size of the `name` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_site_name_blank() -> None:
    """Check that the `name` field cannot be blank (doesn't accept an empty string)."""
    assert not Site._meta.get_field('name').blank


def test_site_name_null() -> None:
    """Check that the `name` field cannot be NULL (doesn't accept `None`)."""
    assert not Site._meta.get_field('name').null


def test_site_name_type() -> None:
    """Check that the `name` field type is `models.CharField`."""
    assert Site._meta.get_field('name').__class__ == models.CharField


# Test Site.code field

def test_site_code_label() -> None:
    """Check that the `code` field label (`verbose_name`) is as expected."""
    assert Site._meta.get_field('code').verbose_name == 'Code'


def test_site_code_max_length() -> None:
    """Check that the size of the `code` field is as expected."""
    assert Site._meta.get_field('code').max_length == 10


# TODO: Check that the min size of the `code` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_site_code_blank() -> None:
    """Check that the `code` field cannot be blank (doesn't accept an empty string)."""
    assert not Site._meta.get_field('code').blank


def test_site_code_null() -> None:
    """Check that the `code` field cannot be NULL (doesn't accept `None`)."""
    assert not Site._meta.get_field('code').null


def test_site_code_type() -> None:
    """Check that the `code` field type is `models.CharField`."""
    assert Site._meta.get_field('code').__class__ == models.CharField


def test_site_code_unique() -> None:
    """Check that the `code` field is unique."""
    assert Site._meta.get_field('code').unique  # type: ignore


# Test Site.parking_url field

def test_site_parking_url_label() -> None:
    """Check that the `parking_url` field label (`verbose_name`) is as expected."""
    assert Site._meta.get_field('parking_url').verbose_name == 'Parking Info (URL)'


def test_site_parking_url_max_length() -> None:
    """Check that the size of the `parking_url` field is as expected."""
    assert Site._meta.get_field('parking_url').max_length == 200


# TODO: Check that the min size of the `parking_url` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_site_parking_url_blank() -> None:
    """Check that the `parking_url` field cannot be blank (doesn't accept an empty string)."""
    assert not Site._meta.get_field('parking_url').blank


def test_site_parking_url_null() -> None:
    """Check that the `parking_url` field cannot be NULL (doesn't accept `None`)."""
    assert not Site._meta.get_field('parking_url').null


def test_site_parking_url_type() -> None:
    """Check that the `parking_url` field type is `models.URLField`."""
    assert Site._meta.get_field('parking_url').__class__ == models.URLField


# Test Site.direction_url field

def test_site_direction_url_label() -> None:
    """Check that the `direction_url` field label (`verbose_name`) is as expected."""
    assert Site._meta.get_field('direction_url').verbose_name == 'Getting to the Hospital (URL)'


def test_site_direction_url_max_length() -> None:
    """Check that the size of the `direction_url` field is as expected."""
    assert Site._meta.get_field('direction_url').max_length == 200


# TODO: Check that the min size of the `direction_url` field is as expected.
# A validator needs to be added to the field.
# https://docs.djangoproject.com/en/4.0/ref/validators/#minlengthvalidator


def test_site_direction_url_blank() -> None:
    """Check that the `direction_url` field cannot be blank (doesn't accept an empty string)."""
    assert not Site._meta.get_field('direction_url').blank


def test_site_direction_url_null() -> None:
    """Check that the `direction_url` field cannot be NULL (doesn't accept `None`)."""
    assert not Site._meta.get_field('direction_url').null


def test_site_direction_url_type() -> None:
    """Check that the `direction_url` field type is `models.URLField`."""
    assert Site._meta.get_field('direction_url').__class__ == models.URLField


# Test Site.institution field

def test_site_institution_label() -> None:
    """Check that the `institution` field label (`verbose_name`) is as expected."""
    assert Site._meta.get_field('institution').verbose_name == 'Institution'


def test_site_institution_blank() -> None:
    """Check that the `institution` field cannot be blank (doesn't accept an empty string)."""
    assert not Site._meta.get_field('institution').blank


def test_site_institution_null() -> None:
    """Check that the `institution` field cannot be NULL (doesn't accept `None`)."""
    assert not Site._meta.get_field('institution').null


def test_site_institution_type() -> None:
    """Check that the `institution` field type is `models.ForeignKey`."""
    assert Site._meta.get_field('institution').is_relation
    assert Site._meta.get_field('institution').__class__ == models.ForeignKey
    assert Site._meta.get_field('institution').related_model == Institution
    assert Site._meta.get_field('institution').many_to_one
    # TODO: check Site.on_delete == models.CASCADE


# Test Site verbose names

def test_site_verbose_name() -> None:
    """Check that `Site` verbose name is as expected."""
    assert Site._meta.verbose_name == 'Site'


def test_site_verbose_name_plural() -> None:
    """Check that `Site` verbose plural name is as expected."""
    assert Site._meta.verbose_name_plural == 'Sites'


# Test Site string method

def test_site_string_method(institution: Institution) -> None:
    """Ensure that the `__str__` method is defined for the `Site` model."""
    # Location is abstract and cannot be instantiated directly
    site = Site(name=TEST_HOSPITAL, code='TH', institution=institution)
    assert str(site) == TEST_HOSPITAL


# Test Site ordering

def test_site_ordered() -> None:
    """Ensure that the sites are ordered by name."""
    institution = Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Site.objects.create(name='Test Site', code='TST', institution=institution)
    Site.objects.create(name='ATest Site', code='TST2', institution=institution)
    first = Site.objects.all()[0]
    assert first.name == 'ATest Site'


def test_relationshiptype_str() -> None:
    """Ensure the `__str__` method is defined for the `RelationshipType` model."""
    relationship_type = RelationshipType(name='Test User Patient Relationship Type')
    assert str(relationship_type) == 'Test User Patient Relationship Type'


def test_relationshiptype_duplicate_names() -> None:
    """Ensure that the relationship type name is unique."""
    factories.RelationshipType(name='Self')

    with assertRaisesMessage(IntegrityError, "Duplicate entry 'Self' for key 'name'"):  # type: ignore[arg-type]
        factories.RelationshipType(name='Self')


def test_relationshiptype_min_age_lowerbound() -> None:
    """Ensure the minimum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE - 1

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MIN_AGE
    relationship_type.full_clean()


def test_relationshiptype_min_age_upperbound() -> None:
    """Ensure the minimum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE - 1)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.start_age = constants.RELATIONSHIP_MAX_AGE - 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_lowerbound() -> None:
    """Ensure the maximum age lower bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE

    message = 'Ensure this value is greater than or equal to {0}.'.format(constants.RELATIONSHIP_MIN_AGE + 1)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MIN_AGE + 1
    relationship_type.full_clean()


def test_relationshiptype_max_age_upperbound() -> None:
    """Ensure the maximum age upper bound is validated correctly."""
    relationship_type = factories.RelationshipType()
    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE + 1

    message = 'Ensure this value is less than or equal to {0}.'.format(constants.RELATIONSHIP_MAX_AGE)

    with assertRaisesMessage(ValidationError, message):  # type: ignore[arg-type]
        relationship_type.full_clean()

    relationship_type.end_age = constants.RELATIONSHIP_MAX_AGE
    relationship_type.full_clean()
