from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import date, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Patient, MedicalRecord, PatientDocument
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientSearchSerializer,
    MedicalRecordSerializer, PatientDocumentSerializer, PatientSummarySerializer
)
from shared.permissions.base_permissions import HasPermission

class PatientViewSet(ModelViewSet):
    """
    Patient Management ViewSet
    
    Provides CRUD operations for patient records.
    Supports advanced search and filtering.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'province', 'has_insurance', 'is_active']
    search_fields = ['full_name', 'patient_code', 'phone_number', 'citizen_id']
    ordering_fields = ['full_name', 'created_at', 'date_of_birth']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PATIENT:READ']
        elif self.action == 'create':
            self.required_permissions = ['PATIENT:CREATE']
        elif self.action == 'update':
            self.required_permissions = ['PATIENT:UPDATE']
        elif self.action == 'partial_update':
            self.required_permissions = ['PATIENT:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PATIENT:DELETE']
        else:
            self.required_permissions = ['PATIENT:READ']
        
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        elif self.action == 'list':
            return PatientSummarySerializer
        return PatientSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Advanced Patient Search",
        description="Search patients by multiple criteria including age range",
        parameters=[
            OpenApiParameter('q', str, description="Tìm kiếm theo tên, mã BN, SĐT, CCCD"),
            OpenApiParameter('age_from', int, description="Tuổi từ"),
            OpenApiParameter('age_to', int, description="Tuổi đến"),
        ],
        responses={200: PatientSummarySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced Patient Search
        
        Search patients by multiple criteria including age range.
        """
        serializer = PatientSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        # Text search
        q = serializer.validated_data.get('q')
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q) |
                Q(patient_code__icontains=q) |
                Q(phone_number__icontains=q) |
                Q(citizen_id__icontains=q)
            )
        
        # Age range filtering
        age_from = serializer.validated_data.get('age_from')
        age_to = serializer.validated_data.get('age_to')
        
        if age_from is not None or age_to is not None:
            today = date.today()
            
            if age_to is not None:
                date_from = today.replace(year=today.year - age_to - 1)
                queryset = queryset.filter(date_of_birth__gt=date_from)
            
            if age_from is not None:
                date_to = today.replace(year=today.year - age_from)
                queryset = queryset.filter(date_of_birth__lte=date_to)
        
        # Other filters
        for field in ['gender', 'province', 'has_insurance', 'is_active']:
            value = serializer.validated_data.get(field)
            if value is not None:
                queryset = queryset.filter(**{field: value})
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PatientSummarySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PatientSummarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get Medical Records",
        description="Returns all medical records for the specified patient",
        responses={200: MedicalRecordSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        """
        Get Medical Records for Patient
        
        Returns all medical records for the specified patient.
        """
        patient = self.get_object()
        records = patient.medical_records.all()
        serializer = MedicalRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get Documents",
        description="Returns all uploaded documents for the specified patient",
        responses={200: PatientDocumentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """
        Get Documents for Patient
        
        Returns all uploaded documents for the specified patient.
        """
        patient = self.get_object()
        documents = patient.documents.all()
        serializer = PatientDocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        summary="Patient Statistics",
        description="Returns various statistics about patients",
        responses={200: dict}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Patient Statistics
        
        Returns various statistics about patients.
        """
        from django.db.models import Count, Case, When
        from django.utils import timezone
        
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stats = Patient.objects.aggregate(
            total_patients=Count('id'),
            new_patients_this_month=Count(
                Case(When(created_at__gte=month_start, then='id'))
            ),
            patients_with_insurance=Count(
                Case(When(has_insurance=True, then='id'))
            ),
            active_patients=Count(
                Case(When(is_active=True, then='id'))
            )
        )
        
        return Response(stats)

class MedicalRecordViewSet(ModelViewSet):
    """
    Medical Record Management ViewSet
    
    Manages patient medical records and visit information.
    """
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'visit_type', 'status', 'department']
    ordering_fields = ['visit_date', 'created_at']
    ordering = ['-visit_date']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PATIENT:READ']
        elif self.action == 'create':
            self.required_permissions = ['PATIENT:CREATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PATIENT:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PATIENT:DELETE']
        
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            doctor=self.request.user if self.request.user.user_type == 'DOCTOR' else None
        )
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class PatientDocumentViewSet(ModelViewSet):
    """
    Patient Document Management ViewSet
    
    Manages patient document uploads and retrieval.
    """
    queryset = PatientDocument.objects.all()
    serializer_class = PatientDocumentSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['patient', 'document_type']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PATIENT:READ']
        elif self.action == 'create':
            self.required_permissions = ['PATIENT:UPDATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PATIENT:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PATIENT:DELETE']
        
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

@extend_schema(
    summary="Validate BHYT Insurance",
    description="Validates insurance card with BHXH system and returns patient info",
    responses={
        200: dict,
        400: dict
    }
)
@api_view(['POST'])
def validate_insurance(request):
    """
    Validate BHYT Insurance
    
    Validates insurance card with BHXH system and returns patient info.
    This is a mock implementation - in production, this would integrate
    with the actual BHXH API.
    """
    insurance_number = request.data.get('insurance_number')
    
    if not insurance_number:
        return Response(
            {'error': 'Insurance number is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mock validation logic
    # In production, this would call BHXH API
    mock_response = {
        'valid': True,
        'patient_info': {
            'full_name': 'Nguyễn Văn A',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'address': 'Hà Nội',
        },
        'coverage_info': {
            'valid_from': '2024-01-01',
            'valid_to': '2024-12-31',
            'hospital_code': 'HN001',
            'coverage_level': '100%'
        }
    }
    
    return Response(mock_response)