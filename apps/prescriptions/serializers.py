from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    DrugCategory, Drug, Prescription, PrescriptionItem, 
    PrescriptionDispensing, DrugInteraction
)

User = get_user_model()

# Simple serializers for nested data
class SimplePatientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    citizen_id = serializers.CharField()
    phone_number = serializers.CharField()
    date_of_birth = serializers.DateField()
    address = serializers.CharField()
    patient_code = serializers.CharField()

class SimpleDoctorSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    full_name = serializers.CharField(source='user.full_name')
    specialization = serializers.CharField()
    license_number = serializers.CharField()

class DrugCategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    drugs_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DrugCategory
        fields = [
            'id', 'code', 'name', 'description', 'parent', 'parent_name',
            'subcategories_count', 'drugs_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_subcategories_count(self, obj):
        return obj.subcategories.filter(is_active=True).count()
    
    def get_drugs_count(self, obj):
        return obj.drugs.filter(is_active=True).count()

class DrugSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    # Display fields
    dosage_form_display = serializers.CharField(source='get_dosage_form_display', read_only=True)
    unit_display = serializers.CharField(source='get_unit_display', read_only=True)
    
    class Meta:
        model = Drug
        fields = [
            'id', 'code', 'name', 'generic_name', 'brand_name',
            'category', 'category_name', 'dosage_form', 'dosage_form_display',
            'strength', 'unit', 'unit_display',
            'indication', 'contraindication', 'side_effects', 'interactions',
            'dosage_adult', 'dosage_child', 'storage_condition', 'expiry_after_opening',
            'unit_price', 'insurance_price',
            'current_stock', 'minimum_stock', 'maximum_stock', 
            'stock_status', 'is_low_stock',
            'registration_number', 'manufacturer', 'country_of_origin',
            'is_prescription_required', 'is_controlled_substance', 'is_active',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'stock_status', 'is_low_stock', 'created_at', 'updated_at']

class DrugSearchSerializer(serializers.Serializer):
    """Serializer for drug search parameters"""
    q = serializers.CharField(required=False, help_text="Tìm theo tên, mã thuốc, hoạt chất")
    category = serializers.UUIDField(required=False, help_text="ID nhóm thuốc")
    dosage_form = serializers.ChoiceField(choices=Drug.FORM_CHOICES, required=False)
    is_prescription_required = serializers.BooleanField(required=False)
    is_low_stock = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)

class PrescriptionItemSerializer(serializers.ModelSerializer):
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_code = serializers.CharField(source='drug.code', read_only=True)
    drug_unit = serializers.CharField(source='drug.get_unit_display', read_only=True)
    drug_generic_name = serializers.CharField(source='drug.generic_name', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)
    
    # For backward compatibility and detailed view
    drug = DrugSerializer(read_only=True)
    
    # Computed fields
    quantity_remaining = serializers.ReadOnlyField()
    is_fully_dispensed = serializers.ReadOnlyField()
    dispensing_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'prescription', 'drug', 'drug_name', 'drug_code', 'drug_unit', 'drug_generic_name',
            'quantity', 'dosage_per_time', 'frequency', 'frequency_display',
            'route', 'route_display', 'duration_days', 'instructions', 'special_notes',
            'unit_price', 'total_price', 'quantity_dispensed', 'quantity_remaining',
            'is_fully_dispensed', 'dispensing_progress', 'is_substitutable',
            'created_at'
        ]
        read_only_fields = [
            'id', 'prescription', 'unit_price', 'total_price', 'quantity_dispensed',
            'quantity_remaining', 'is_fully_dispensed', 'dispensing_progress',
            'created_at'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    # Flat fields for compatibility
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_code = serializers.CharField(source='patient.patient_code', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone_number', read_only=True)
    
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    # Nested objects for detailed view
    patient = SimplePatientSerializer(read_only=True)
    doctor = SimpleDoctorSerializer(read_only=True)
    
    # Status and validity
    is_valid = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prescription_type_display = serializers.CharField(source='get_prescription_type_display', read_only=True)
    
    # Include prescription items
    items = PrescriptionItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_number', 
            # Flat fields
            'patient_name', 'patient_code', 'patient_phone',
            'doctor_name', 'doctor_specialization', 
            # Nested objects
            'patient', 'doctor', 'appointment',
            'prescription_date', 'prescription_type', 'prescription_type_display',
            'status', 'status_display', 'diagnosis', 'notes', 'special_instructions',
            'valid_from', 'valid_until', 'is_valid', 'days_until_expiry',
            'total_amount', 'insurance_covered_amount', 'patient_payment_amount',
            'items', 'items_count', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'prescription_number', 'is_valid', 'days_until_expiry',
            'total_amount', 'insurance_covered_amount', 'patient_payment_amount',
            'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'patient', 'doctor', 'appointment', 'prescription_type',
            'diagnosis', 'notes', 'special_instructions',
            'valid_from', 'valid_until', 'items'
        ]
    
    def validate_items(self, items):
        print(f"🔍 validate_items called with: {items}")
        print(f"🔍 Items type: {type(items)}")
        
        if not items:
            raise serializers.ValidationError("Đơn thuốc phải có ít nhất 1 loại thuốc")
        
        # Validate each item
        for i, item_data in enumerate(items):
            print(f"🔍 Item {i}: {item_data} (type: {type(item_data)})")
            
            drug_id = item_data.get('drug')
            if drug_id and hasattr(drug_id, 'pk'):
                drug = drug_id
            else:
                try:
                    from .models import Drug
                    drug = Drug.objects.get(id=drug_id)
                except Drug.DoesNotExist:
                    raise serializers.ValidationError(f"Không tìm thấy thuốc với ID: {drug_id}")
            
            # Check stock availability
            quantity = item_data.get('quantity', 0)
            if quantity > drug.current_stock:
                raise serializers.ValidationError(
                    f"Thuốc {drug.name} không đủ tồn kho. Có sẵn: {drug.current_stock}, yêu cầu: {quantity}"
                )
        
        return items
    
    def validate(self, attrs):
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until:
            if valid_from >= valid_until:
                raise serializers.ValidationError({
                    'valid_until': 'Thời hạn kết thúc phải sau thời hạn bắt đầu'
                })
            
            # Check reasonable validity period (max 6 months)
            max_days = (valid_until - valid_from).days
            if max_days > 180:
                raise serializers.ValidationError({
                    'valid_until': 'Thời hạn đơn thuốc không được quá 6 tháng'
                })
        
        return attrs
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Set default validity if not provided
        if not validated_data.get('valid_from'):
            validated_data['valid_from'] = timezone.now()
        
        if not validated_data.get('valid_until'):
            validated_data['valid_until'] = validated_data['valid_from'] + timedelta(days=30)
        
        prescription = Prescription.objects.create(**validated_data)
        
        # Create prescription items
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        
        # Recalculate totals
        prescription.calculate_total_amount()
        prescription.calculate_insurance_amounts()
        prescription.save()
        
        return prescription

class PrescriptionDispenseSerializer(serializers.ModelSerializer):
    pharmacist_name = serializers.CharField(source='pharmacist.full_name', read_only=True)
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    drug_name = serializers.CharField(source='prescription_item.drug.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PrescriptionDispensing
        fields = [
            'id', 'prescription', 'prescription_number', 'prescription_item',
            'drug_name', 'quantity_dispensed', 'batch_number', 'expiry_date',
            'pharmacist', 'pharmacist_name', 'status', 'status_display',
            'dispensed_at', 'notes'
        ]
        read_only_fields = ['id', 'dispensed_at']

class PrescriptionDispenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionDispensing
        fields = [
            'prescription_item', 'quantity_dispensed', 'batch_number', 
            'expiry_date', 'notes'
        ]
    
    def validate(self, attrs):
        prescription_item = attrs['prescription_item']
        quantity_dispensed = attrs['quantity_dispensed']
        
        # Require payment before dispensing: patient must have at least one PAID payment
        prescription = prescription_item.prescription
        try:
            from apps.payments.models import Payment
            has_paid = Payment.objects.filter(prescription=prescription, status='PAID').exists()
        except Exception:
            has_paid = False
        if not has_paid:
            raise serializers.ValidationError("Đơn thuốc chưa được thanh toán. Vui lòng thanh toán trước khi cấp thuốc.")

        # Check if prescription is still valid
        if not prescription_item.prescription.is_valid:
            raise serializers.ValidationError("Đơn thuốc đã hết hạn hoặc không còn hiệu lực")
        
        # Check remaining quantity
        if quantity_dispensed > prescription_item.quantity_remaining:
            raise serializers.ValidationError(
                f"Số lượng cấp ({quantity_dispensed}) vượt quá số lượng còn lại ({prescription_item.quantity_remaining})"
            )
        
        # Check drug stock
        if quantity_dispensed > prescription_item.drug.current_stock:
            raise serializers.ValidationError(
                f"Không đủ tồn kho. Có sẵn: {prescription_item.drug.current_stock}, yêu cầu: {quantity_dispensed}"
            )
        
        return attrs
    
    def create(self, validated_data):
        # Set pharmacist from request user
        validated_data['pharmacist'] = self.context['request'].user
        validated_data['status'] = 'DISPENSED'
        
        dispense_record = PrescriptionDispensing.objects.create(**validated_data)
        
        # Update drug stock
        drug = dispense_record.prescription_item.drug
        drug.current_stock -= dispense_record.quantity_dispensed
        drug.save()
        
        return dispense_record

class DrugInteractionSerializer(serializers.ModelSerializer):
    drug1_name = serializers.CharField(source='drug1.name', read_only=True)
    drug2_name = serializers.CharField(source='drug2.name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = DrugInteraction
        fields = [
            'id', 'drug1', 'drug1_name', 'drug2', 'drug2_name',
            'severity', 'severity_display', 'description', 'clinical_effect',
            'management', 'is_active', 'created_at'
        ]

class PrescriptionStatsSerializer(serializers.Serializer):
    """Serializer for prescription statistics"""
    total_prescriptions = serializers.IntegerField()
    active_prescriptions = serializers.IntegerField()
    expired_prescriptions = serializers.IntegerField()
    dispensed_prescriptions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=0)
    insurance_covered = serializers.DecimalField(max_digits=15, decimal_places=0)

class DrugInventorySerializer(serializers.Serializer):
    """Serializer for drug inventory alerts"""
    drug_id = serializers.UUIDField()
    drug_name = serializers.CharField()
    current_stock = serializers.IntegerField()
    minimum_stock = serializers.IntegerField()
    status = serializers.CharField()