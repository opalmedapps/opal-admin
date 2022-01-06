from django.db import models
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(_('Code'), max_length=10, unique=True)

    def __str__(self) -> str:
        return self.name


class Institution(Location):
    class Meta:
        ordering = ['name']


class Site(Location):
    class Meta:
        ordering = ['name']

    parking_url = models.URLField(_('Parking Info'))
    institution = models.ForeignKey(
        to=Institution,
        on_delete=models.CASCADE,
        related_name='sites',
        verbose_name=_('Institution'),
    )
