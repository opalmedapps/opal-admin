import pytest

from .. import factories

pytestmark = pytest.mark.django_db()


def test_coded_element_factory() -> None:
    """Ensure the `CodedElement` factory creates a valid model."""
    codedelement = factories.CodedElementFactory()
    codedelement.full_clean()


def test_physician_prescription_order_factory() -> None:
    """Ensure the `PhysicianPrescriptionOrder` factory creates a valid model."""
    physicianorder = factories.PhysicianPrescriptionOrderFactory()
    physicianorder.full_clean()


def test_pharmacy_encoded_order_factory() -> None:
    """Ensure the `PharmacyEncodedOrder` factory creates a valid model."""
    pharmacyorder = factories.PharmacyEncodedOrderFactory()
    pharmacyorder.full_clean()


def test_pharmacy_route_factory() -> None:
    """Ensure the `PharmacyRoute` factory creates a valid model."""
    pharmacyroute = factories.PharmacyRouteFactory()
    pharmacyroute.full_clean()


def test_pharmacy_component_factory() -> None:
    """Ensure the `PharmacyComponent` factory creates a valid model."""
    pharmacycomponent = factories.CodedElementFactory()
    pharmacycomponent.full_clean()


def test_multi_observations_test() -> None:
    """Ensure multiple component instances can be assigned to one PharmacyEncodedOrder."""
    pharmacyorder = factories.PharmacyEncodedOrderFactory()
    component1 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component2 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component3 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component4 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)
    component5 = factories.PharmacyComponentFactory(pharmacy_encoded_order=pharmacyorder)

    components = [component1, component2, component3, component4, component5]
    for component in components:
        component.full_clean()
