import pytest

from ..models import Institution, Site

TEST_HOSPITAL = 'Test Hospital'

pytestmark = pytest.mark.django_db

# Institution tests


def test_institution_string_method() -> None:
    """Ensure the `__str__` method is defined for the `Institution` model."""
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name=TEST_HOSPITAL, code='TH')
    assert str(institution) == TEST_HOSPITAL


def test_institution_ordered() -> None:
    """Ensure that the institutions are ordered by name."""
    Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Institution.objects.create(name='ATest Hospital', code='TH2')
    first = Institution.objects.all()[0]
    assert first.name == 'ATest Hospital'


def test_institution_name_label(institution: Institution) -> None:
    """This test checks that the `name` field label (`verbose_name`) is as expected."""
    field_label = institution._meta.get_field('name').verbose_name
    assert field_label == 'Name'


def test_institution_name_max_length(institution: Institution) -> None:
    """This test checks that the size of the `name` field is as expected."""
    max_length = institution._meta.get_field('name').max_length
    assert max_length == 100


def test_institution_code_label(institution: Institution) -> None:
    """This test checks that the `code` field label (`verbose_name`) is as expected."""
    field_label = institution._meta.get_field('code').verbose_name
    assert field_label == 'Code'


def test_institution_code_max_length(institution: Institution) -> None:
    """This test checks that the size of the `code` field is as expected."""
    max_length = institution._meta.get_field('code').max_length
    assert max_length == 10


def test_institution_verbose_name(institution: Institution) -> None:
    """This test checks that `Institution` verbose name is as expected."""
    verbose_name = institution._meta.verbose_name
    assert verbose_name == 'Institution'


def test_institution_verbose_name_plural(institution: Institution) -> None:
    """This test checks that `Institution` verbose plural name is as expected."""
    verbose_name_plural = institution._meta.verbose_name_plural
    assert verbose_name_plural == 'Institutions'

# Site tests


def test_site_name_label(site: Site) -> None:
    """This test checks that the `name` field label (`verbose_name`) is as expected."""
    field_label = site._meta.get_field('name').verbose_name
    assert field_label == 'Name'


def test_site_name_max_length(site: Site) -> None:
    """This test checks that the size of the `name` field is as expected."""
    max_length = site._meta.get_field('name').max_length
    assert max_length == 100


def test_site_code_label(site: Site) -> None:
    """This test checks that the `code` field label (`verbose_name`) is as expected."""
    field_label = site._meta.get_field('code').verbose_name
    assert field_label == 'Code'


def test_site_code_max_length(site: Site) -> None:
    """This test checks that the size of the `code` field is as expected."""
    max_length = site._meta.get_field('code').max_length
    assert max_length == 10


def test_site_verbose_name(site: Site) -> None:
    """This test checks that `Site` verbose name is as expected."""
    verbose_name = site._meta.verbose_name
    assert verbose_name == 'Site'


def test_site_verbose_name_plural(site: Site) -> None:
    """This test checks that `Site` verbose plural name is as expected."""
    verbose_name_plural = site._meta.verbose_name_plural
    assert verbose_name_plural == 'Sites'


def test_site_parking_url_label(site: Site) -> None:
    """This test checks that the `parking_url` field label (`verbose_name`) is as expected."""
    field_label = site._meta.get_field('parking_url').verbose_name
    assert field_label == 'Parking Info'


def test_site_string_method(institution: Institution) -> None:
    """Ensure the `__str__` method is defined for the `Site` model."""
    # Location is abstract and cannot be instantiated directly
    site = Site(name=TEST_HOSPITAL, code='TH', institution=institution)
    assert str(site) == TEST_HOSPITAL


def test_site_ordered() -> None:
    """Ensure that the sites are ordered by name."""
    institution = Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Site.objects.create(name='Test Site', code='TST', institution=institution)
    Site.objects.create(name='ATest Site', code='TST2', institution=institution)
    first = Site.objects.all()[0]
    assert first.name == 'ATest Site'
