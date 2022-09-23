"""This module provides Django REST framework serializers for hospital-specific settings models."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer

from ..models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a `Site` is serialized for an API."""

    # since urls has the app_name the URL field needs to be defined here with the appropriate view_name
    # see: https://stackoverflow.com/q/20550598
    url = serializers.HyperlinkedIdentityField(view_name='api:sites-detail')

    class Meta:
        model = Site
        fields = ['id', 'url', 'name', 'code', 'direction_url', 'parking_url', 'longitude', 'latitude']


class InstitutionSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsSerializer):
    """This class defines how a `Site` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-detail')
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = ['id', 'url', 'name', 'code', 'sites']
