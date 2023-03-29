"""Collection of serializers for the app ApiViews."""

from rest_framework import serializers

from opal.core.api.serializers import DynamicFieldsSerializer
from opal.legacy.models import LegacyAlias, LegacyAppointment, LegacyHospitalMap, LegacyPatient


class LegacyAliasSerializer(DynamicFieldsSerializer):
    """Serializer for the `LegacyAlias` model."""

    class Meta:
        model = LegacyAlias
        fields = ['aliassernum', 'aliastype', 'aliasname_en', 'aliasname_fr']


class LegacyHospitalMapSerializer(DynamicFieldsSerializer):
    """Serializer for the `LegacyHospitalMap` model."""

    class Meta:
        model = LegacyHospitalMap
        fields = [
            'hospitalmapsernum',
            'mapurl_en',
            'mapurl_fr',
            'mapname_en',
            'mapname_fr',
            'mapdescription_en',
            'mapdescription_fr',
        ]


class LegacyPatientSerializer(DynamicFieldsSerializer):
    """Serializer for the `LegacyPatient` model."""

    class Meta:
        model = LegacyPatient
        fields = ['patientsernum', 'firstname', 'lastname', 'email', 'ssn']


class LegacyAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for the `LegacyAppointment` model."""

    checkinpossible = serializers.IntegerField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkinpossible',
    )

    class Meta:
        model = LegacyAppointment
        fields = ['appointmentsernum', 'state', 'scheduledstarttime', 'checkin', 'checkinpossible', 'patientsernum']


class LegacyAppointmentDetailedSerializer(serializers.ModelSerializer):
    """Serializer for the `LegacyAppointment` model to get more appointment details."""

    checkinpossible = serializers.IntegerField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkinpossible',
    )

    checkininstruction_en = serializers.CharField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkininstruction_en',
    )

    checkininstruction_fr = serializers.CharField(
        source='aliasexpressionsernum.aliassernum.appointmentcheckin.checkininstruction_fr',
    )

    patient = LegacyPatientSerializer(
        source='patientsernum',
        fields=('patientsernum', 'firstname', 'lastname'),
        many=False,
        read_only=True,
    )

    alias = LegacyAliasSerializer(
        source='aliasexpressionsernum.aliassernum',
        fields=('aliastype', 'aliasname_en', 'aliasname_fr'),
        many=False,
        read_only=True,
    )

    hospitalmap = LegacyHospitalMapSerializer(
        source='aliasexpressionsernum.aliassernum.hospitalmapsernum',
        fields=(
            'mapurl_en',
            'mapurl_fr',
            'mapname_en',
            'mapname_fr',
            'mapdescription_en',
            'mapdescription_fr',
        ),
        many=False,
        read_only=True,
    )

    class Meta:
        model = LegacyAppointment
        fields = [
            'appointmentsernum',
            'state',
            'scheduledstarttime',
            'checkin',
            'checkinpossible',
            'checkininstruction_en',
            'checkininstruction_fr',
            'roomlocation_en',
            'roomlocation_fr',
            'hospitalmap',
            'patient',
            'alias',
        ]


class QuestionnaireReportRequestSerializer(serializers.Serializer):
    """This class defines how a `QuestionnairesReport` request data are serialized."""

    mrn = serializers.CharField(
        max_length=10,
        required=True,
        allow_blank=False,
        min_length=6,
        label='MRN',
    )
    site = serializers.CharField(
        max_length=10,
        required=True,
        allow_blank=False,
        label='Site code',
    )  # TODO: min_length?


class UnreadCountSerializer(serializers.Serializer):
    """Serializer a dictionary having several key-value pairs."""

    unread_appointment_count = serializers.IntegerField()
    unread_document_count = serializers.IntegerField()
    unread_txteammessage_count = serializers.IntegerField()
    unread_educationalmaterial_count = serializers.IntegerField()
    unread_questionnaire_count = serializers.IntegerField()


class AnnouncementUnreadCountSerializer(serializers.Serializer):
    """Serializer for the unread count of Announcement queryset."""

    unread_announcement_count = serializers.IntegerField(min_value=0)
