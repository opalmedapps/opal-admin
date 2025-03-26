"""This module provides models for core settings."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Address(models.Model):
    """Abstract class representing a generalized address with details."""

    street_name = models.CharField(_('Street Name'), default='', max_length=100)
    street_number = models.CharField(_('Street Number'), default='', max_length=100)
    postal_code = models.CharField(_('Postal Code'), default='XXXXXX', max_length=6)
    city = models.CharField(_('City'), default='', max_length=100)
    province_code = models.CharField(_('Province Code'), default='', max_length=2)
    contact_telephone = models.CharField(_('Contact Telephone'), default='', max_length=100)
    contact_fax = models.CharField(_('Contact Fax'), default='', max_length=100, blank=True)

    class Meta:
        abstract = True
