import pytest

from .. import factories

pytestmark = pytest.mark.django_db()


def test_databankconsent_factory() -> None:
    """Ensure the `DatabankConsent` factory creates a valid model."""
    databank_consent = factories.DatabankConsent()

    databank_consent.full_clean()


def test_quantitysample_str() -> None:
    """Ensure the `__str__` method is defined for the `DatabankConsent` model."""
    databank_consent = factories.DatabankConsent()
    databank_consent.full_clean()

    assert str(databank_consent) == "Bart Simpson's Databank Consent"
