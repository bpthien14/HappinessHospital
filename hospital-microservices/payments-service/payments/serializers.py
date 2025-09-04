from rest_framework import serializers
from .models import Payment, PaymentReceipt, VNPayTransaction
import uuid


class PrescriptionField(serializers.Field):
    """Custom field to accept either UUID or prescription number (Microservice version)"""
    
    def to_internal_value(self, data):
        # In microservice architecture, we'll validate prescription_id as UUID
        # The actual prescription validation will be done via API call to Prescriptions Service
        
        if not data:
            raise serializers.ValidationError('Prescription ID is required')
        
        # Try to parse as UUID
        try:
            uuid.UUID(str(data))
            return data  # Return the UUID string
        except ValueError:
            raise serializers.ValidationError('Prescription ID must be a valid UUID')
    
    def to_representation(self, value):
        return str(value) if value else None


class PaymentSerializer(serializers.ModelSerializer):
    prescription_id = serializers.UUIDField(read_only=True)
    created_by_id = serializers.UUIDField(read_only=True)
    vnpay_payment_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'prescription_id', 'method', 'amount', 'currency',
            'status', 'vnpay_payment_url',
            'vnp_TxnRef', 'vnp_Amount', 'vnp_OrderInfo', 'vnp_ResponseCode',
            'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate',
            'created_by_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'created_by_id', 'created_at', 'updated_at',
            'vnpay_payment_url', 'vnp_ResponseCode', 'vnp_TransactionNo', 
            'vnp_BankCode', 'vnp_PayDate'
        ]

    def get_vnpay_payment_url(self, obj):
        """Get VNPAY payment URL if method is VNPAY"""
        if obj.method == 'VNPAY' and obj.status == 'PENDING':
            return obj.get_vnpay_payment_url()
        return None



class PaymentCreateSerializer(serializers.ModelSerializer):
    prescription_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES)

    class Meta:
        model = Payment
        fields = ['prescription_id', 'method']

    def validate_prescription_id(self, prescription_id):
        """Validate prescription exists via Prescriptions Service API"""
        # TODO: Make API call to Prescriptions Service to validate prescription
        # For now, just validate UUID format
        try:
            uuid.UUID(str(prescription_id))
            return prescription_id
        except ValueError:
            raise serializers.ValidationError('Invalid prescription ID format')
        
        # TODO: Add actual validation against Prescriptions Service
        # response = requests.get(f"{settings.PRESCRIPTIONS_SERVICE_URL}/api/prescriptions/{prescription_id}/")
        # if response.status_code != 200:
        #     raise serializers.ValidationError('Prescription not found')

    def validate(self, attrs):
        prescription_id = attrs['prescription_id']
        
        # TODO: Get prescription amount from Prescriptions Service
        # For now, we'll require amount to be provided
        if 'amount' not in attrs:
            raise serializers.ValidationError('Amount is required')
        
        amount = attrs['amount']
        if amount <= 0:
            raise serializers.ValidationError('Amount must be greater than 0')

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Get user ID from JWT token or Auth Service
            validated_data['created_by_id'] = str(request.user.id) if hasattr(request.user, 'id') else None
        else:
            validated_data['created_by_id'] = None
            
        payment = Payment.objects.create(**validated_data)
        return payment


class VNPayCreateSerializer(serializers.Serializer):
    prescription_id = serializers.UUIDField()
    order_desc = serializers.CharField(max_length=255, help_text="Mô tả đơn hàng")
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, help_text="Số tiền thanh toán")

    def validate_prescription_id(self, prescription_id):
        """Validate prescription exists via Prescriptions Service API"""
        try:
            uuid.UUID(str(prescription_id))
            return prescription_id
        except ValueError:
            raise serializers.ValidationError('Invalid prescription ID format')
        
        # TODO: Add actual validation against Prescriptions Service
        # response = requests.get(f"{settings.PRESCRIPTIONS_SERVICE_URL}/api/prescriptions/{prescription_id}/")
        # if response.status_code != 200:
        #     raise serializers.ValidationError('Prescription not found')

    def validate(self, attrs):
        prescription_id = attrs['prescription_id']
        amount = attrs['amount']
        
        if amount <= 0:
            raise serializers.ValidationError('Amount must be greater than 0')
        
        # TODO: Validate amount against prescription amount from Prescriptions Service
        
        return attrs


class CashPaymentConfirmSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


class PaymentReceiptSerializer(serializers.ModelSerializer):
    cashier_id = serializers.UUIDField(source='cashier_id', read_only=True)

    class Meta:
        model = PaymentReceipt
        fields = ['id', 'payment', 'receipt_number', 'cashier_id', 'note', 'created_at']
        read_only_fields = ['id', 'receipt_number', 'cashier_id', 'created_at']


class VNPayTransactionSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(source='payment.id', read_only=True)
    
    class Meta:
        model = VNPayTransaction
        fields = [
            'id', 'payment', 'payment_id', 'vnp_TxnRef', 'vnp_Amount',
            'vnp_OrderInfo', 'vnp_CreateDate', 'vnp_IpAddr', 'vnp_ResponseCode',
            'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
