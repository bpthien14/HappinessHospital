from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Payment, PaymentReceipt, VNPayTransaction
import uuid

User = get_user_model()


class PrescriptionField(serializers.Field):
    """Custom field to accept either UUID or prescription number"""
    
    def to_internal_value(self, data):
        from apps.prescriptions.models import Prescription
        
        if not data:
            raise serializers.ValidationError('Prescription is required')
        
        # Try to parse as UUID first
        try:
            uuid.UUID(str(data))
            # It's a valid UUID, lookup by ID
            try:
                return Prescription.objects.get(id=data)
            except Prescription.DoesNotExist:
                raise serializers.ValidationError('Đơn thuốc không tồn tại')
        except ValueError:
            # Not a UUID, try prescription number
            try:
                return Prescription.objects.get(prescription_number=data)
            except Prescription.DoesNotExist:
                raise serializers.ValidationError(f'Không tìm thấy đơn thuốc với số: {data}')
    
    def to_representation(self, value):
        return str(value.id) if value else None


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
            'vnpay_payment_url', 'vnp_ResponseCode', 'vnp_TransactionNo', 
            'vnp_BankCode', 'vnp_PayDate'
        ]

    def get_vnpay_payment_url(self, obj):
        """Get VNPAY payment URL if method is VNPAY"""
        if obj.method == 'VNPAY' and obj.status == 'PENDING':
            return obj.get_vnpay_payment_url()
        return None



class PaymentCreateSerializer(serializers.ModelSerializer):
    prescription = PrescriptionField()
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)

    class Meta:
        model = Payment
        fields = ['prescription', 'method']

    def validate_prescription(self, prescription):
        """Validate prescription status and payment eligibility"""
        
        # Check if prescription is cancelled or expired
        if prescription.status in ['CANCELLED', 'EXPIRED']:
            raise serializers.ValidationError(
                f'Không thể thanh toán đơn thuốc đã {prescription.get_status_display().lower()}'
            )
        
        # Check if prescription is already fully dispensed
        if prescription.status == 'FULLY_DISPENSED':
            raise serializers.ValidationError('Đơn thuốc đã được cấp thuốc đầy đủ')
        
        # Check if there's already a PAID payment for this prescription
        existing_paid = Payment.objects.filter(
            prescription=prescription, 
            status='PAID'
        ).exists()
        if existing_paid:
            raise serializers.ValidationError('Đơn thuốc đã được thanh toán')
        
        return prescription

    def validate(self, attrs):
        prescription = attrs['prescription']

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
    prescription = PrescriptionField()
    order_desc = serializers.CharField(max_length=255, help_text="Mô tả đơn hàng")
    use_qr_code = serializers.BooleanField(default=False, help_text="Sử dụng QR code thay vì redirect")

    def validate_prescription(self, prescription):
        """Validate prescription for VNPAY payment"""
        
        # Check if prescription is cancelled or expired
        if prescription.status in ['CANCELLED', 'EXPIRED']:
            raise serializers.ValidationError(
                f'Không thể thanh toán đơn thuốc đã {prescription.get_status_display().lower()}'
            )
        
        # Check if prescription is already fully dispensed
        if prescription.status == 'FULLY_DISPENSED':
            raise serializers.ValidationError('Đơn thuốc đã được cấp thuốc đầy đủ')
        
        # Check if there's already a PAID payment for this prescription
        existing_paid = Payment.objects.filter(
            prescription=prescription, 
            status='PAID'
        ).exists()
        if existing_paid:
            raise serializers.ValidationError('Đơn thuốc đã được thanh toán')
        
        return prescription

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