# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""This module provides Django REST framework serializers for hospital-specific settings models."""

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.core.drf_fields import Base64FileField

from ..models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer[Site]):
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
            'acronym',
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


class InstitutionSerializer(serializers.HyperlinkedModelSerializer[Institution], DynamicFieldsSerializer[Institution]):
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
            'acronym',
            'support_email',
            'adulthood_age',
            'non_interpretable_lab_result_delay',
            'interpretable_lab_result_delay',
            'sites',
        ]


class TermsOfUseSerializer(serializers.HyperlinkedModelSerializer[Institution]):
    """This class defines how the `terms of use` of an `Institution` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-terms-of-use')
    terms_of_use_en = Base64FileField()
    terms_of_use_fr = Base64FileField()

    class Meta:
        model = Institution
        fields = ['id', 'url', 'terms_of_use_en', 'terms_of_use_fr']
