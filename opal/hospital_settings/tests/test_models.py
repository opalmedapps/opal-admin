from ..models import Institution


def test_location_string():
    # Location is abstract and cannot be instantiated directly
    institution = Institution(name='Test Hospital', code='TH')

    assert str(institution) == 'Test Hospital'
