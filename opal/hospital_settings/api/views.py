from rest_framework import permissions, viewsets

from ..models import Institution, Site
from .serializers import InstitutionSerializer, SiteSerializer


# REST API
class InstitutionViewSet(viewsets.ModelViewSet):
    """
    This viewset provides an API view for ``Institution``.

    It uses the ``InstitutionSerializer`` and allows to filter by institution ``code``.
    """

    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['code']


class SiteViewSet(viewsets.ModelViewSet):
    """
    This viewset provides an API view for ``Site``.

    It uses the ``SiteSerializer`` to serialize a ``Site``.
    It allows to filter by site ``code`` where a comma-separated list of codes
    can be provided for the `code__in` query parameter.
    """

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # see: https://github.com/carltongibson/django-filter/issues/1076#issuecomment-489252242
    filterset_fields = {
        'code': ['in'],
        'institution__code': ['exact'],
    }
