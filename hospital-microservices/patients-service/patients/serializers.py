from rest_framework import serializers
from .models import Patient, MedicalRecord, PatientDocument
from datetime import date
import re

class PatientSerializer(serializers.ModelSerializer):
    """Full Patient serializer with all fields"""
    age = serializers.ReadOnlyField(help_text="Tuổi tính từ ngày sinh")
    full_address = serializers.ReadOnlyField(help_text="Địa chỉ đầy đủ")
    insurance_status = serializers.ReadOnlyField(help_text="Trạng thái BHYT")
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_code', 'full_name', 'date_of_birth', 'age', 'gender',
            'phone_number', 'email', 'address', 'ward', 'province',
            'full_address', 'citizen_id', 'blood_type', 'allergies', 'chronic_diseases',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'has_insurance', 'insurance_number', 'insurance_valid_from', 'insurance_valid_to',
            'insurance_hospital_code', 'insurance_status',
            'created_by_id', 'updated_by_id',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'patient_code', 'age', 'full_address', 'insurance_status',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'full_name': {'help_text': 'Họ và tên đầy đủ'},
            'phone_number': {'help_text': 'Số điện thoại theo định dạng Việt Nam'},
            'citizen_id': {'help_text': 'Số CCCD/CMND (9 hoặc 12 số)'},
            'insurance_number': {'help_text': 'Số thẻ BHYT (nếu có)'},
        }
    
    def validate_insurance_fields(self, attrs):
        """Validate insurance-related fields"""
        has_insurance = attrs.get('has_insurance', False)
        
        if has_insurance:
            insurance_number = attrs.get('insurance_number')
            insurance_valid_from = attrs.get('insurance_valid_from')
            insurance_valid_to = attrs.get('insurance_valid_to')
            
            if not insurance_number:
                raise serializers.ValidationError("Số thẻ BHYT là bắt buộc khi có BHYT")
            
            if insurance_valid_from and insurance_valid_to:
                if insurance_valid_from >= insurance_valid_to:
                    raise serializers.ValidationError("Ngày hiệu lực BHYT không hợp lệ")
        
        return attrs
    
    def validate(self, attrs):
        # Normalize phone numbers: keep '+' and digits only
        phone_number = attrs.get('phone_number', '')
        if phone_number:
            # Remove all non-digit characters except '+'
            normalized_phone = re.sub(r'[^\d+]', '', phone_number)
            if normalized_phone.startswith('+84'):
                normalized_phone = normalized_phone
            elif normalized_phone.startswith('84'):
                normalized_phone = '+' + normalized_phone
            elif normalized_phone.startswith('0'):
                normalized_phone = '+84' + normalized_phone[1:]
            else:
                normalized_phone = '+84' + normalized_phone
            
            attrs['phone_number'] = normalized_phone
        
        # Validate insurance fields
        attrs = self.validate_insurance_fields(attrs)
        
        return attrs

class PatientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new patients"""
    class Meta:
        model = Patient
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'address', 'ward', 'province', 'citizen_id',
            'blood_type', 'allergies', 'chronic_diseases',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'has_insurance', 'insurance_number', 'insurance_valid_from', 'insurance_valid_to',
            'insurance_hospital_code'
        ]
        extra_kwargs = {
            'full_name': {'required': True},
            'date_of_birth': {'required': True},
            'gender': {'required': True},
            'phone_number': {'required': True},
            'address': {'required': True},
            'ward': {'required': True},
            'province': {'required': True},
            'citizen_id': {'required': True},
            'emergency_contact_name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'emergency_contact_phone': {'required': False, 'allow_null': True, 'allow_blank': True},
            'emergency_contact_relationship': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        # Normalize phone numbers
        phone_number = attrs.get('phone_number', '')
        if phone_number:
            normalized_phone = re.sub(r'[^\d+]', '', phone_number)
            if normalized_phone.startswith('+84'):
                normalized_phone = normalized_phone
            elif normalized_phone.startswith('84'):
                normalized_phone = '+' + normalized_phone
            elif normalized_phone.startswith('0'):
                normalized_phone = '+84' + normalized_phone[1:]
            else:
                normalized_phone = '+84' + normalized_phone
            
            attrs['phone_number'] = normalized_phone
        
        # Validate insurance fields
        has_insurance = attrs.get('has_insurance', False)
        if has_insurance:
            insurance_number = attrs.get('insurance_number')
            if not insurance_number:
                raise serializers.ValidationError("Số thẻ BHYT là bắt buộc khi có BHYT")
        
        return attrs

class PatientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating patients"""
    class Meta:
        model = Patient
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'address', 'ward', 'province', 'citizen_id',
            'blood_type', 'allergies', 'chronic_diseases',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'has_insurance', 'insurance_number', 'insurance_valid_from', 'insurance_valid_to',
            'insurance_hospital_code', 'is_active'
        ]
        extra_kwargs = {
            'full_name': {'required': False},
            'date_of_birth': {'required': False},
            'gender': {'required': False},
            'phone_number': {'required': False},
            'address': {'required': False},
            'ward': {'required': False},
            'province': {'required': False},
            'citizen_id': {'required': False},
        }

class PatientSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for patient lists"""
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_code', 'full_name', 'age', 'gender',
            'phone_number', 'province', 'full_address', 'has_insurance',
            'is_active', 'created_at'
        ]

class MedicalRecordSerializer(serializers.ModelSerializer):
    """Medical Record serializer"""
    blood_pressure = serializers.ReadOnlyField()
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'medical_record_number', 'patient_id', 'doctor_id',
            'visit_date', 'visit_type', 'department', 'status',
            'chief_complaint', 'history_of_present_illness', 'physical_examination',
            'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'weight', 'height',
            'preliminary_diagnosis', 'final_diagnosis', 'treatment_plan', 'notes',
            'next_appointment', 'follow_up_instructions',
            'created_by_id', 'updated_by_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'medical_record_number', 'created_at', 'updated_at']

class MedicalRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating medical records"""
    class Meta:
        model = MedicalRecord
        fields = [
            'patient_id', 'doctor_id', 'visit_date', 'visit_type', 'department',
            'chief_complaint', 'history_of_present_illness', 'physical_examination',
            'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'weight', 'height',
            'preliminary_diagnosis', 'final_diagnosis', 'treatment_plan', 'notes',
            'next_appointment', 'follow_up_instructions'
        ]
        extra_kwargs = {
            'patient_id': {'required': True},
            'visit_date': {'required': True},
            'visit_type': {'required': True},
            'department': {'required': True},
            'chief_complaint': {'required': True},
        }

class PatientDocumentSerializer(serializers.ModelSerializer):
    """Patient Document serializer"""
    class Meta:
        model = PatientDocument
        fields = [
            'id', 'patient_id', 'document_type', 'title', 'description',
            'file_url', 'file_size', 'uploaded_by_id', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']

class PatientDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating patient documents"""
    class Meta:
        model = PatientDocument
        fields = [
            'patient_id', 'document_type', 'title', 'description',
            'file_url', 'file_size'
        ]
        extra_kwargs = {
            'patient_id': {'required': True},
            'document_type': {'required': True},
            'title': {'required': True},
            'file_url': {'required': True},
        }
