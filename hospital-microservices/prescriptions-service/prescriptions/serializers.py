from rest_framework import serializers
from .models import DrugCategory, Drug, Prescription, PrescriptionItem, PrescriptionDispensing

class DrugCategorySerializer(serializers.ModelSerializer):
    """Drug Category serializer"""
    class Meta:
        model = DrugCategory
        fields = [
            'id', 'code', 'name', 'description',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DrugSerializer(serializers.ModelSerializer):
    """Full Drug serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.ReadOnlyField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'code', 'name', 'generic_name', 'brand_name',
            'category', 'category_name', 'dosage_form', 'strength', 'unit',
            'indication', 'contraindication', 'side_effects', 'interactions',
            'dosage_adult', 'dosage_child', 'storage_condition', 'expiry_after_opening',
            'unit_price', 'insurance_price', 'current_stock', 'minimum_stock', 'maximum_stock',
            'registration_number', 'manufacturer', 'country_of_origin',
            'is_prescription_required', 'is_controlled_substance', 'is_active',
            'stock_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stock_status', 'created_at', 'updated_at'
        ]

class DrugCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating drugs"""
    class Meta:
        model = Drug
        fields = [
            'code', 'name', 'generic_name', 'brand_name', 'category',
            'dosage_form', 'strength', 'unit', 'indication', 'contraindication',
            'side_effects', 'interactions', 'dosage_adult', 'dosage_child',
            'storage_condition', 'expiry_after_opening', 'unit_price', 'insurance_price',
            'current_stock', 'minimum_stock', 'maximum_stock', 'registration_number',
            'manufacturer', 'country_of_origin', 'is_prescription_required',
            'is_controlled_substance', 'is_active'
        ]

class DrugUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating drugs"""
    class Meta:
        model = Drug
        fields = [
            'name', 'generic_name', 'brand_name', 'category', 'dosage_form',
            'strength', 'unit', 'indication', 'contraindication', 'side_effects',
            'interactions', 'dosage_adult', 'dosage_child', 'storage_condition',
            'expiry_after_opening', 'unit_price', 'insurance_price',
            'current_stock', 'minimum_stock', 'maximum_stock', 'registration_number',
            'manufacturer', 'country_of_origin', 'is_prescription_required',
            'is_controlled_substance', 'is_active'
        ]

class DrugSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for drug lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.ReadOnlyField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'code', 'name', 'category_name', 'dosage_form', 'strength',
            'unit_price', 'current_stock', 'stock_status', 'is_active'
        ]

class DrugInventorySerializer(serializers.ModelSerializer):
    """Serializer for drug inventory management"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.ReadOnlyField()
    
    class Meta:
        model = Drug
        fields = [
            'id', 'code', 'name', 'category_name', 'current_stock',
            'minimum_stock', 'maximum_stock', 'stock_status'
        ]

class PrescriptionItemSerializer(serializers.ModelSerializer):
    """Prescription Item serializer"""
    drug_name = serializers.CharField(source='drug.name', read_only=True)
    drug_code = serializers.CharField(source='drug.code', read_only=True)
    drug_unit = serializers.CharField(source='drug.unit', read_only=True)
    
    quantity_remaining = serializers.ReadOnlyField()
    is_fully_dispensed = serializers.ReadOnlyField()
    dispensing_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = PrescriptionItem
        fields = [
            'id', 'prescription', 'drug', 'drug_name', 'drug_code', 'drug_unit',
            'quantity', 'dosage_per_time', 'frequency', 'route', 'duration_days',
            'instructions', 'special_notes', 'unit_price', 'total_price',
            'quantity_dispensed', 'quantity_remaining', 'is_fully_dispensed',
            'dispensing_progress', 'is_substitutable', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_price', 'quantity_remaining', 'is_fully_dispensed',
            'dispensing_progress', 'created_at'
        ]

class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescription items"""
    class Meta:
        model = PrescriptionItem
        fields = [
            'drug', 'quantity', 'dosage_per_time', 'frequency', 'route',
            'duration_days', 'instructions', 'special_notes', 'is_substitutable'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    """Full Prescription serializer"""
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
            'id', 'prescription_number', 'patient_id', 'doctor_id', 'appointment_id',
            'prescription_date', 'prescription_type', 'prescription_type_display',
            'status', 'status_display', 'diagnosis', 'notes', 'special_instructions',
            'valid_from', 'valid_until', 'is_valid', 'days_until_expiry',
            'total_amount', 'insurance_covered_amount', 'patient_payment_amount',
            'items', 'items_count', 'created_by_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'prescription_number', 'is_valid', 'days_until_expiry',
            'total_amount', 'insurance_covered_amount', 'patient_payment_amount',
            'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescriptions"""
    items = PrescriptionItemCreateSerializer(many=True, write_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'patient_id', 'doctor_id', 'appointment_id', 'prescription_type',
            'diagnosis', 'notes', 'special_instructions', 'valid_from', 'valid_until',
            'items'
        ]
        extra_kwargs = {
            'patient_id': {'required': True},
            'doctor_id': {'required': True},
            'diagnosis': {'required': True},
            'valid_from': {'required': True},
            'valid_until': {'required': True},
            'items': {'required': True},
        }
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        prescription = Prescription.objects.create(**validated_data)
        
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        
        return prescription

class PrescriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating prescriptions"""
    class Meta:
        model = Prescription
        fields = [
            'status', 'diagnosis', 'notes', 'special_instructions',
            'valid_from', 'valid_until'
        ]

class PrescriptionSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for prescription lists"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prescription_type_display = serializers.CharField(source='get_prescription_type_display', read_only=True)
    is_valid = serializers.ReadOnlyField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_number', 'patient_id', 'doctor_id', 'appointment_id',
            'prescription_date', 'prescription_type', 'prescription_type_display',
            'status', 'status_display', 'diagnosis', 'is_valid',
            'total_amount', 'items_count', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()

class PrescriptionDispensingSerializer(serializers.ModelSerializer):
    """Prescription Dispensing serializer"""
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    drug_name = serializers.CharField(source='prescription_item.drug.name', read_only=True)
    
    class Meta:
        model = PrescriptionDispensing
        fields = [
            'id', 'prescription', 'prescription_number', 'prescription_item', 'drug_name',
            'quantity_dispensed', 'batch_number', 'expiry_date', 'pharmacist_id',
            'status', 'dispensed_at', 'notes'
        ]
        read_only_fields = [
            'id', 'dispensed_at'
        ]

class PrescriptionDispensingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prescription dispensing"""
    class Meta:
        model = PrescriptionDispensing
        fields = [
            'prescription', 'prescription_item', 'quantity_dispensed',
            'batch_number', 'expiry_date', 'pharmacist_id', 'notes'
        ]
        extra_kwargs = {
            'prescription': {'required': True},
            'prescription_item': {'required': True},
            'quantity_dispensed': {'required': True},
            'expiry_date': {'required': True},
            'pharmacist_id': {'required': True},
        }
