"""This module provides Django REST framework serializers for hospital-specific settings models."""
from typing import Optional

from rest_framework import serializers

from ...core.drf_fields import Base64PDFFileField
from ..models import Institution, Site


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a `Site` is serialized for an API."""

    # since urls has the app_name the URL field needs to be defined here with the appropriate view_name
    # see: https://stackoverflow.com/q/20550598
    url = serializers.HyperlinkedIdentityField(view_name='api:sites-detail')

    class Meta:
        model = Site
        fields = ['id', 'url', 'name', 'code', 'direction_url', 'parking_url', 'longitude', 'latitude']


class InstitutionSerializer(serializers.HyperlinkedModelSerializer):
    """This class defines how a `Site` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-detail')
    sites = SiteSerializer(many=True, read_only=True)

    class Meta:
        model = Institution
        fields = ['id', 'url', 'name', 'code', 'sites']


class TermsOfUseSerialiser(serializers.HyperlinkedModelSerializer):
    """This class defines how the `terms of use` of an `Institution` is serialized for an API."""

    url = serializers.HyperlinkedIdentityField(view_name='api:institutions-retrieve-terms-of-use')
    terms_of_use_encoded = serializers.SerializerMethodField('get_terms_of_use_encoded')

    class Meta:
        model = Institution
        fields = ['id', 'url', 'terms_of_use_encoded']

    def get_terms_of_use_encoded(self, obj: Institution) -> Optional[str]:  # noqa: WPS615
        """Get the terms of use content in base64 encoded form.

        Args:
            obj (Institution): Input Institution

        Returns:
            str: encoded base64 string of the file content
            if the 'terms_of_use' field is a valid pdf file, `None` otherwise
        """
        pdf_field = Base64PDFFileField()
        return pdf_field.to_representation(obj.terms_of_use.path)
