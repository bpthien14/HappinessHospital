from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Payment, PaymentReceipt, VNPayTransaction


User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    vnpay_payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'prescription', 'prescription_number', 'method', 'amount', 'currency',
            'status', 'vnpay_payment_url',
            'vnp_TxnRef', 'vnp_Amount', 'vnp_OrderInfo', 'vnp_ResponseCode',
            'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'created_by', 'created_by_name', 'created_at', 'updated_at',
            'vnpay_payment_url', 'vnp_ResponseCode', 'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate'
        ]

    def get_vnpay_payment_url(self, obj):
        """Get VNPAY payment URL if method is VNPAY"""
        if obj.method == 'VNPAY' and obj.status == 'PENDING':
            return obj.get_vnpay_payment_url()
        return None


class PaymentCreateSerializer(serializers.ModelSerializer):
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)

    class Meta:
        model = Payment
        fields = ['prescription', 'method']

    def validate(self, attrs):
        prescription = attrs['prescription']

        # Must be active and not fully dispensed
        if prescription.status in ['CANCELLED', 'EXPIRED']:
            raise serializers.ValidationError('Đơn thuốc không hợp lệ để thanh toán')

        # Calculate due amount
        amount = Payment.calculate_due_amount(prescription)
        if amount <= 0:
            raise serializers.ValidationError('Đơn thuốc không có số tiền phải thanh toán')

        attrs['amount'] = amount
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        payment = Payment.objects.create(**validated_data)
        return payment


class VNPayCreateSerializer(serializers.Serializer):
    prescription = serializers.UUIDField()
    order_desc = serializers.CharField(max_length=255, help_text="Mô tả đơn hàng")

    def validate_prescription(self, value):
        from apps.prescriptions.models import Prescription
        try:
            prescription = Prescription.objects.get(id=value)
            if prescription.status in ['CANCELLED', 'EXPIRED']:
                raise serializers.ValidationError('Đơn thuốc không hợp lệ để thanh toán')
            return prescription
        except Prescription.DoesNotExist:
            raise serializers.ValidationError('Đơn thuốc không tồn tại')

    def validate(self, attrs):
        prescription = attrs['prescription']
        amount = Payment.calculate_due_amount(prescription)
        if amount <= 0:
            raise serializers.ValidationError('Đơn thuốc không có số tiền phải thanh toán')
        
        attrs['amount'] = amount
        return attrs


class CashPaymentConfirmSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class PaymentReceiptSerializer(serializers.ModelSerializer):
    cashier_name = serializers.CharField(source='cashier.full_name', read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_number', 'cashier', 'cashier_name', 'note', 'created_at']
        read_only_fields = ['id', 'receipt_number', 'cashier', 'cashier_name', 'created_at']


class VNPayTransactionSerializer(serializers.ModelSerializer):
    payment_number = serializers.CharField(source='payment.prescription.prescription_number', read_only=True)
    
    class Meta:
        model = VNPayTransaction
        fields = [
            'id', 'payment', 'payment_number', 'vnp_TxnRef', 'vnp_Amount',
            'vnp_OrderInfo', 'vnp_CreateDate', 'vnp_IpAddr', 'vnp_ResponseCode',
            'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']