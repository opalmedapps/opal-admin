"""This module provides views for the hospital-specific settings REST API."""
from rest_framework import exceptions, generics

from opal.core.drf_permissions import FullDjangoModelPermissions

from ..models import Institution
from .serializers import InstitutionSerializer


class RetrieveInstitutionView(generics.RetrieveAPIView):
    """
    This view provides an API view to retrieve the singleton `Institution`.

    It uses the `InstitutionSerializer` to serialize data.
    """

    permission_classes = (FullDjangoModelPermissions,)
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer

    def get_object(self) -> Institution:
        """
        Return the singleton Institution instance.

        Returns:
            the institution instance

        Raises:
            APIException: if there is more than one institution
        """
        try:
            institution: Institution = generics.get_object_or_404(self.get_queryset())
        except Institution.MultipleObjectsReturned:
            raise exceptions.APIException('There is more than one institution')

        # May raise a permission denied
        self.check_object_permissions(self.request, institution)

        return institution
