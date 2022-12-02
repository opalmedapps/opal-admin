from typing import Any
from typing_extensions import reveal_type

from rest_framework import serializers

from ..models import QuantitySample


class QuantitySampleListSerializer(serializers.ListSerializer):

    def create(self, validated_data: Any) -> Any:
        print('list create')
        print(reveal_type(validated_data))
        return QuantitySample.objects.bulk_create(QuantitySample(**data) for data in validated_data)
        # return super().create(validated_data)


class QuantitySampleSerializer(serializers.ModelSerializer):
    def create(self, validated_data: Any):
        # add data_store reference to create a new instance
        validated_data['data_store'] = self.context['data_store']
        print(f'create {validated_data}')

        return super().create(validated_data)

    class Meta:
        model = QuantitySample
        fields = ('value', 'type', 'start_date', 'source')
        list_serializer_class = QuantitySampleListSerializer
