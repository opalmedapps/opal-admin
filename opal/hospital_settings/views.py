from rest_framework import permissions, viewsets

from .models import Institution, Site
from .serializers import InstitutionSerializer, SiteSerializer


class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['code']


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # see: https://github.com/carltongibson/django-filter/issues/1076#issuecomment-489252242
    filterset_fields = {
        'code': ['in'],
        'institution__code': ['exact'],
    }
