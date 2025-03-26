"""This module provides Django REST framework serializers for hospital-specific settings models."""
from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.core.drf_fields import Base64FileField

from ..models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a `Site` is serialized for an API."""

    # since urls has the app_name the URL field needs to be defined here with the appropriate view_name
    # see: https://stackoverflow.com/q/20550598
    url = serializers.HyperlinkedIdentityField(view_name='api:sites-detail')

    class Meta:
        model = Site
        fields = [
            'id',
            'url',
            'name',
            'code',
            'direction_url',
            'parking_url',
            'longitude',
            'latitude',
            'street_name',
            'street_number',
            'postal_code',
            'city',
            'province_code',
            'contact_telephone',
            'contact_fax',
        ]


class InstitutionSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsSerializer):
    """
    This class defines how an `Institution` model is serialized for the REST API.

    It inherits from core.api.serializers.DynamicFieldsSerializer,
    and also provides the site code according to the 'fields' arguments.
    """

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-detail')
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = [
            'id',
            'url',
            'name',
            'code',
            'support_email',
            'adulthood_age',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
            'sites',
            'registration_code_valid_period',
        ]


class TermsOfUseSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how the `terms of use` of an `Institution` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-terms-of-use')
    terms_of_use = Base64FileField()

    class Meta:
        model = Institution
        fields = ['id', 'url', 'terms_of_use']
