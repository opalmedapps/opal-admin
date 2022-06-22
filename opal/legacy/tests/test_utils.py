import pytest

from opal.legacy import factories, models
from opal.legacy.utils import get_patient_sernum

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_user_sernum() -> None:
    """Test get_patient_sernum method."""
    factories.LegacyUserFactory()
    user = models.LegacyUsers.objects.all()[0]
    sernum = get_patient_sernum(user.username)
    assert sernum == user.usertypesernum


def test_get_user_sernum_no_user_available() -> None:
    """Test get_patient_sernum method when no user are found."""
    sernum = get_patient_sernum('random_string')
    assert sernum == 0
