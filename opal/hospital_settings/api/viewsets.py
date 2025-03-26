"""This module provides `ViewSets` for the hospital-specific settings REST API."""
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import Institution, Site
from .serializers import InstitutionSerializer, SiteSerializer, TermsOfUseSerialiser


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset provides an API view for `Institution`.

    It uses the `InstitutionSerializer` and allows to filter by institution `code`.
    """

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    filterset_fields = ['code']

    def retrieve_terms_of_use(self, request: Request, pk: int) -> Response:
        """Retrieve the terms of use content from the backend.

        Args:
            request: The Request details
            pk: The primary key of the Institution

        Returns:
            Response: encoded base64 string of the file content
            if the 'terms_of_use' field is a valid pdf file, `None` otherwise
        """
        institution_object = self.get_object()
        input_serializer = TermsOfUseSerialiser(institution_object, many=False, context={'request': request})
        return Response(input_serializer.data)


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset provides an API view for `Site`.

    It uses the `SiteSerializer` to serialize a `Site`.
    It allows to filter by site `code` where a comma-separated list of codes
    can be provided for the `code__in` query parameter.
    """

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    # see: https://github.com/carltongibson/django-filter/issues/1076#issuecomment-489252242
    filterset_fields = {
        'code': ['in'],
        'institution__code': ['exact'],
    }
