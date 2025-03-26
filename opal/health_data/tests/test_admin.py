from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

from ..admin import AbstractSampleAdminMixin, QuantitySampleAdmin
from ..models import QuantitySample

site = AdminSite()


def test_abstractsampleadmin_cannot_change() -> None:
    """The `AbstractSampleAdminMixin` has no change permission."""
    admin = AbstractSampleAdminMixin()
    request = HttpRequest()
    instance = QuantitySample()

    assert admin.has_change_permission(request, None) is False
    assert admin.has_change_permission(request, instance) is False


def test_abstractsampleadmin_cannot_delete() -> None:
    """The `AbstractSampleAdminMixin` has no delete permission."""
    admin = AbstractSampleAdminMixin()
    request = HttpRequest()
    instance = QuantitySample()

    assert admin.has_delete_permission(request, None) is False
    assert admin.has_delete_permission(request, instance) is False


def test_quantitysample_cannot_change() -> None:
    """The `QuantitySampleAdmin` has no change permission."""
    admin = QuantitySampleAdmin(QuantitySample, site)
    request = HttpRequest()
    instance = QuantitySample()

    assert admin.has_change_permission(request, None) is False
    assert admin.has_change_permission(request, instance) is False


def test_quantitysample_cannot_delete() -> None:
    """The `QuantitySampleAdmin` has no delete permission."""
    admin = QuantitySampleAdmin(QuantitySample, site)
    request = HttpRequest()
    instance = QuantitySample()

    assert admin.has_delete_permission(request, None) is False
    assert admin.has_delete_permission(request, instance) is False
