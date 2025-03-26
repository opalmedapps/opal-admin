import pytest

from opal.legacy import factories, models
from opal.legacy import utils as legacy_utils

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_user_sernum() -> None:
    """Test get_patient_sernum method."""
    factories.LegacyUserFactory()
    user = models.LegacyUsers.objects.all()[0]
    sernum = legacy_utils.get_patient_sernum(user.username)
    assert sernum == user.usertypesernum


def test_get_user_sernum_no_user_available() -> None:
    """Test get_patient_sernum method when no user are found."""
    sernum = legacy_utils.get_patient_sernum('random_string')
    assert sernum == 0


def test_update_legacy_user_type() -> None:
    """Ensure that a legacy user's type can be updated."""
    legacy_user = factories.LegacyUserFactory(usertype=models.LegacyUserType.CAREGIVER)
    legacy_utils.update_legacy_user_type(legacy_user.usersernum, models.LegacyUserType.PATIENT)
    legacy_user.refresh_from_db()

    assert legacy_user.usertype == models.LegacyUserType.PATIENT
