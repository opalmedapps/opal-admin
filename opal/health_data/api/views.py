from typing import Any, Dict
import random

from django.db.models import QuerySet

from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import QuantitySampleSerializer
from ..models import HealthDataStore, QuantitySample


class CreateQuantitySampleView(generics.ListCreateAPIView):
    serializer_class = QuantitySampleSerializer
    pagination_class = None


    def get_queryset(self) -> QuerySet[QuantitySample]:
        print('get_queryset')
        patient_id = self.kwargs['patient_id']
        # queryset = HealthDataStore.objects.filter(patient__id=patient_id).prefetch_related('quantity_samples')
        # data_store = generics.get_object_or_404(queryset)
        # return data_store.quantity_samples.all()
        return QuantitySample.objects.filter(data_store__patient__id=patient_id)

    def get_serializer_context(self) -> Dict[str, Any]:
        patient_id = self.kwargs.get('patient_id')
        queryset = HealthDataStore.objects.filter(patient__id=patient_id).prefetch_related('quantity_samples')
        data_store = generics.get_object_or_404(queryset)
        print('get_serializer_context')
        print(data_store)

        context = super().get_serializer_context()
        context.update({'data_store': data_store})

        return context

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        print(serializer)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
