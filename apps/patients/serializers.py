from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, MedicalRecord, PatientDocument
from datetime import date
import re
from rest_framework.validators import UniqueValidator

User = get_user_model()

class PatientSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField(help_text="Tuổi tính từ ngày sinh")
    full_address = serializers.ReadOnlyField(help_text="Địa chỉ đầy đủ")
    insurance_status = serializers.ReadOnlyField(help_text="Trạng thái BHYT")
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_code', 'full_name', 'date_of_birth', 'age', 'gender',
            'phone_number', 'email', 'address', 'ward', 'province',
            'full_address', 'citizen_id', 'blood_type', 'allergies', 'chronic_diseases',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'has_insurance', 'insurance_number', 'insurance_valid_from', 'insurance_valid_to',
            'insurance_hospital_code', 'insurance_status',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'patient_code', 'age', 'full_address', 'insurance_status',
            'created_by', 'updated_by', 'created_at', 'updated_at'
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
            if not attrs.get('insurance_number'):
                raise serializers.ValidationError({
                    'insurance_number': 'Số thẻ BHYT là bắt buộc khi có BHYT'
                })
        
        return attrs
    
    def validate(self, attrs):
        attrs = self.validate_insurance_fields(attrs)
        return attrs

class PatientCreateSerializer(serializers.ModelSerializer):
    citizen_id = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=Patient.objects.all(),
                message="Bệnh nhân có CMND/CCCD đã tồn tại."
            )
        ]
    )
    phone_number = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=Patient.objects.all(),
                message="Số điện thoại đã tồn tại."
            )
        ]
    )
    
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
            # district removed
            'province': {'required': True},
            'citizen_id': {'required': True},
            # emergency contact nullable
            'emergency_contact_name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'emergency_contact_phone': {'required': False, 'allow_null': True, 'allow_blank': True},
            'emergency_contact_relationship': {'required': False, 'allow_null': True, 'allow_blank': True},
        }
    
    def validate(self, attrs):
        # Normalize phone numbers: keep '+' and digits only
        for phone_field in ['phone_number', 'emergency_contact_phone']:
            phone_value = attrs.get(phone_field)
            if phone_value:
                normalized = re.sub(r'[^\d+]', '', str(phone_value))
                attrs[phone_field] = normalized

        # Normalize citizen_id: remove spaces
        if attrs.get('citizen_id'):
            attrs['citizen_id'] = str(attrs['citizen_id']).replace(' ', '')

        # Validate age <= 100 and not in the future
        dob = attrs.get('date_of_birth')
        if dob:
            today = date.today()
            if dob > today:
                raise serializers.ValidationError({'date_of_birth': 'Ngày sinh không được ở tương lai'})
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age > 100:
                raise serializers.ValidationError({'date_of_birth': 'Tuổi không được vượt quá 100'})

        return PatientSerializer().validate(attrs)

class PatientSearchSerializer(serializers.Serializer):
    """Serializer for patient search parameters"""
    q = serializers.CharField(required=False, help_text="Tìm kiếm theo tên, mã BN, SĐT, CCCD")
    gender = serializers.ChoiceField(choices=Patient.GENDER_CHOICES, required=False)
    age_from = serializers.IntegerField(min_value=0, max_value=150, required=False)
    age_to = serializers.IntegerField(min_value=0, max_value=150, required=False)
    province = serializers.CharField(required=False)
    has_insurance = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False, default=True)

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_code = serializers.CharField(source='patient.patient_code', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    blood_pressure = serializers.ReadOnlyField(help_text="Huyết áp (systolic/diastolic)")
    bmi = serializers.ReadOnlyField(help_text="Chỉ số BMI")
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'medical_record_number', 'patient', 'patient_name', 'patient_code',
            'doctor', 'doctor_name', 'visit_date', 'visit_type', 'department', 'status',
            'chief_complaint', 'history_of_present_illness', 'physical_examination',
            'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_pressure',
            'heart_rate', 'respiratory_rate', 'weight', 'height', 'bmi',
            'preliminary_diagnosis', 'final_diagnosis', 'treatment_plan', 'notes',
            'next_appointment', 'follow_up_instructions',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'medical_record_number', 'blood_pressure', 'bmi',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]

class PatientDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientDocument
        fields = [
            'id', 'patient', 'document_type', 'title', 'description',
            'file', 'file_url', 'file_size', 'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_by', 'uploaded_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class PatientSummarySerializer(serializers.ModelSerializer):
    """Simplified patient serializer for lists and references"""
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Patient
        fields = [
            'id', 'patient_code', 'full_name', 'date_of_birth', 'age',
            'gender', 'phone_number', 'insurance_status'
        ]