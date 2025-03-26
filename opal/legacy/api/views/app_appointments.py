"""Collection of api views used to get appointment details."""
from django.db.models.query import QuerySet

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from opal.legacy import models

from ..serializers import LegacyAppointmentDetailedSerializer


class AppAppointmentsView(ListAPIView):
    """Class to return appointments detail data."""

    queryset = models.LegacyAppointment.objects.select_related(
        'aliasexpressionsernum',
        'aliasexpressionsernum__aliassernum',
        'aliasexpressionsernum__aliassernum__appointmentcheckin',
    ).exclude(
        status='Deleted',
    ).order_by('appointmentsernum')

    permission_classes = [IsAuthenticated]

    serializer_class = LegacyAppointmentDetailedSerializer

    def get_queryset(self) -> QuerySet[models.LegacyAppointment]:
        """
        Override get_queryset to filter appointments by appointmentsernums.

        Returns:
            The list of legacy appointments
        """
        if 'ids' in self.request.data:
            return super().get_queryset().filter(
                appointmentsernum__in=self.request.data['ids'],
            )
        return super().get_queryset()
