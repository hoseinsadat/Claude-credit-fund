from rest_framework import serializers

from apps.clients.models import Client
from apps.guarantees.models import FeeSchedule, Guarantee, GuaranteeType, Payment
from apps.notifications.models import Notification
from apps.portal.models import GuaranteeRequest


class GuaranteeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuaranteeType
        fields = ('id', 'code', 'name_fa', 'typical_duration_months')


class GuaranteeRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuaranteeRequest
        fields = ('id', 'guarantee_type', 'beneficiary_name', 'beneficiary_info',
                  'requested_amount', 'purpose', 'requested_duration_months')

    def create(self, validated_data):
        user = self.context['request'].user
        client = user.client_profile
        return GuaranteeRequest.objects.create(
            client=client,
            submitted_by=user,
            **validated_data,
        )


class GuaranteeRequestListSerializer(serializers.ModelSerializer):
    guarantee_type_name = serializers.CharField(source='guarantee_type.name_fa', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GuaranteeRequest
        fields = ('id', 'guarantee_type', 'guarantee_type_name', 'beneficiary_name',
                  'requested_amount', 'purpose', 'requested_duration_months',
                  'status', 'status_display', 'reviewer_notes', 'created_at')
        read_only_fields = fields


class GuaranteeListSerializer(serializers.ModelSerializer):
    guarantee_type_name = serializers.CharField(source='guarantee_type.name_fa', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    beneficiary_name = serializers.CharField(source='beneficiary.name', read_only=True)

    class Meta:
        model = Guarantee
        fields = ('id', 'guarantee_number', 'guarantee_type_name', 'beneficiary_name',
                  'amount', 'state', 'state_display', 'issue_date', 'expiry_date', 'created_at')
        read_only_fields = fields


class GuaranteeDetailSerializer(serializers.ModelSerializer):
    guarantee_type_name = serializers.CharField(source='guarantee_type.name_fa', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    beneficiary_name = serializers.CharField(source='beneficiary.name', read_only=True)
    fees = serializers.SerializerMethodField()

    class Meta:
        model = Guarantee
        fields = ('id', 'guarantee_number', 'guarantee_type_name', 'beneficiary_name',
                  'amount', 'currency', 'state', 'state_display',
                  'deposit_amount', 'commission_rate', 'commission_amount',
                  'issue_date', 'effective_date', 'expiry_date', 'purpose',
                  'renewal_count', 'fees', 'created_at')
        read_only_fields = fields

    def get_fees(self, obj):
        return FeeScheduleSerializer(obj.fee_schedules.all(), many=True).data


class FeeScheduleSerializer(serializers.ModelSerializer):
    fee_type_display = serializers.CharField(source='get_fee_type_display', read_only=True)

    class Meta:
        model = FeeSchedule
        fields = ('id', 'fee_type', 'fee_type_display', 'amount', 'due_date', 'is_paid')
        read_only_fields = fields


class PaymentListSerializer(serializers.ModelSerializer):
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'payment_type', 'payment_type_display', 'amount',
                  'payment_method', 'payment_method_display', 'reference_number',
                  'payment_date', 'is_verified')
        read_only_fields = fields


class ClientProfileSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    available_credit = serializers.DecimalField(max_digits=20, decimal_places=0, read_only=True)

    class Meta:
        model = Client
        fields = ('id', 'client_code', 'client_type', 'display_name',
                  'credit_limit', 'used_credit', 'available_credit', 'is_active')
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'body', 'channel', 'is_read', 'read_at', 'created_at')
        read_only_fields = fields


class DashboardSerializer(serializers.Serializer):
    active_guarantees_count = serializers.IntegerField()
    total_exposure = serializers.DecimalField(max_digits=20, decimal_places=0)
    pending_requests = serializers.IntegerField()
    pending_fees = serializers.DecimalField(max_digits=20, decimal_places=0)
