"""This module provides Django REST framework serializers for hospital-specific settings models."""
from rest_framework import serializers

from .models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a ``Site`` is serialized for an API."""

    # since urls has the app_name the URL field needs to be defined here with the appropriate view_name
    # see: https://stackoverflow.com/q/20550598
    url = serializers.HyperlinkedIdentityField(view_name='hospital-settings:site-detail')
    # define specific serializer field for institution
    # need to define view_name specifically
    institution = serializers.HyperlinkedRelatedField(
        queryset=Institution.objects.all(),
        view_name='hospital-settings:institution-detail',
    )

    class Meta:
        model = Site
        fields = ['id', 'url', 'name', 'code', 'parking_url']


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a ``Site`` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='hospital-settings:institution-detail')
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = ['id', 'url', 'name', 'code', 'sites']
