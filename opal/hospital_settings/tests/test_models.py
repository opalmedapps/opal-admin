import pytest

from ..models import Institution, Site

TEST_HOSPITAL = 'Test Hospital'


def test_location_string():
    """This test ensures the __str__ method is defined."""
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name=TEST_HOSPITAL, code='TH')

    assert str(institution) == TEST_HOSPITAL


@pytest.mark.django_db()
def test_institution_ordered():
    """This test ensures that the institutions are ordered by name."""
    Institution.objects.create(name=TEST_HOSPITAL, code='TH')
    Institution.objects.create(name='ATest Hospital', code='TH2')

    first = Institution.objects.all()[0]

    assert first.name == 'ATest Hospital'


@pytest.mark.django_db()
def test_site_ordered():
    """This test ensures that the sites are ordered by name."""
    institution = Institution.objects.create(name=TEST_HOSPITAL, code='TH')

    Site.objects.create(name='Test Site', code='TST', institution=institution)
    Site.objects.create(name='ATest Site', code='TST2', institution=institution)

    first = Site.objects.all()[0]

    assert first.name == 'ATest Site'
