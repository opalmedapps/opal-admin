"""This module provides `ViewSets` for the hospital-specific settings REST API."""
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from opal.core.drf_permissions import FullDjangoModelPermissions

from ..models import Institution, Site
from .serializers import InstitutionSerializer, SiteSerializer, TermsOfUseSerializer


class InstitutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset provides an API view for `Institution`.

    It uses the `InstitutionSerializer` and allows to filter by institution `acronym`.
    """

    permission_classes = (FullDjangoModelPermissions,)
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    filterset_fields = ['acronym']

    def retrieve_terms_of_use(self, request: Request, pk: int) -> Response:
        """
        REST API method for handling HTTP requests to retrieve `Institution's` terms of use PDF file in base64 format.

        Args:
            request: HTTP GET request
            pk: primary key of an `Institution`

        Returns:
            Response: HTTP response containing JSON object with `Institution's` terms of use PDF file in base64 format.
        """
        serializer = TermsOfUseSerializer(self.get_object(), many=False, context={'request': request})
        return Response(serializer.data)


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset provides an API view for `Site`.

    It uses the `SiteSerializer` to serialize a `Site`.
    It allows to filter by site `acronym` where a comma-separated list of acronyms
    can be provided for the `acronym__in` query parameter.
    """

    permission_classes = (FullDjangoModelPermissions,)
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    # see: https://github.com/carltongibson/django-filter/issues/1076#issuecomment-489252242
    filterset_fields = {
        'acronym': ['in'],
        'institution__acronym': ['exact'],
    }
