import pytest

from ..models import Institution, Site


def test_location_string():
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name='Test Hospital', code='TH')

    assert str(institution) == 'Test Hospital'


@pytest.mark.django_db
def test_institution_ordered():
    Institution.objects.create(name='Test Hospital', code='TH')
    Institution.objects.create(name='ATest Hospital', code='TH2')

    first = Institution.objects.all()[0]

    assert first.name == 'ATest Hospital'


@pytest.mark.django_db
def test_site_ordered():
    institution = Institution.objects.create(name='Test Hospital', code='TH')

    Site.objects.create(name='Test Site', code='TST', institution=institution)
    Site.objects.create(name='ATest Site', code='TST2', institution=institution)

    first = Site.objects.all()[0]

    assert first.name == 'ATest Site'
