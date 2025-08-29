from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Patient, MedicalRecord, PatientDocument
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientUpdateSerializer, PatientSummarySerializer,
    MedicalRecordSerializer, MedicalRecordCreateSerializer,
    PatientDocumentSerializer, PatientDocumentCreateSerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    """
    Patient Management ViewSet
    
    Provides CRUD operations for patient records.
    Supports advanced search and filtering.
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'province', 'has_insurance', 'is_active']
    search_fields = ['full_name', 'patient_code', 'phone_number', 'citizen_id']
    ordering_fields = ['full_name', 'created_at', 'date_of_birth']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Allow public read access for portal queries
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PatientUpdateSerializer
        elif self.action == 'list':
            return PatientSummarySerializer
        return PatientSerializer
    
    def perform_create(self, serializer):
        # Set created_by_id from request user
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(created_by_id=self.request.user.id, updated_by_id=self.request.user.id)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        # Set updated_by_id from request user
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(updated_by_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List patients",
        description="Get a list of all patients with optional filtering and search",
        parameters=[
            OpenApiParameter(name='search', description='Search by name, code, phone, or ID', required=False),
            OpenApiParameter(name='gender', description='Filter by gender (M/F/O)', required=False),
            OpenApiParameter(name='province', description='Filter by province', required=False),
            OpenApiParameter(name='has_insurance', description='Filter by insurance status', required=False),
            OpenApiParameter(name='is_active', description='Filter by active status', required=False),
        ],
        examples=[
            OpenApiExample(
                'Success Response',
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": "uuid-here",
                            "patient_code": "BN2025080001",
                            "full_name": "Nguyễn Văn A",
                            "age": 30,
                            "gender": "M",
                            "phone_number": "+84901234567",
                            "province": "Hà Nội",
                            "full_address": "123 Đường ABC, Quận 1, Hà Nội",
                            "has_insurance": True,
                            "is_active": True,
                            "created_at": "2025-08-29T10:00:00Z"
                        }
                    ]
                }
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create patient",
        description="Create a new patient record",
        examples=[
            OpenApiExample(
                'Request Body',
                value={
                    "full_name": "Nguyễn Văn A",
                    "date_of_birth": "1995-01-01",
                    "gender": "M",
                    "phone_number": "0901234567",
                    "address": "123 Đường ABC",
                    "ward": "Quận 1",
                    "province": "Hà Nội",
                    "citizen_id": "123456789012"
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get patient details",
        description="Get detailed information about a specific patient"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update patient",
        description="Update an existing patient record"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Partial update patient",
        description="Partially update an existing patient record"
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Delete patient",
        description="Delete a patient record (soft delete by setting is_active=False)"
    )
    def destroy(self, request, *args, **kwargs):
        patient = self.get_object()
        patient.is_active = False
        patient.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="Search patients",
        description="Advanced search for patients with multiple criteria",
        parameters=[
            OpenApiParameter(name='q', description='Search query', required=True),
            OpenApiParameter(name='gender', description='Filter by gender', required=False),
            OpenApiParameter(name='province', description='Filter by province', required=False),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for patients"""
        query = request.query_params.get('q', '')
        gender = request.query_params.get('gender', '')
        province = request.query_params.get('province', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                models.Q(full_name__icontains=query) |
                models.Q(patient_code__icontains=query) |
                models.Q(phone_number__icontains=query) |
                models.Q(citizen_id__icontains=query)
            )
        
        if gender:
            queryset = queryset.filter(gender=gender)
        
        if province:
            queryset = queryset.filter(province__icontains=province)
        
        serializer = PatientSummarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get patient statistics",
        description="Get statistics about patients"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get patient statistics"""
        total_patients = Patient.objects.count()
        active_patients = Patient.objects.filter(is_active=True).count()
        male_patients = Patient.objects.filter(gender='M', is_active=True).count()
        female_patients = Patient.objects.filter(gender='F', is_active=True).count()
        patients_with_insurance = Patient.objects.filter(has_insurance=True, is_active=True).count()
        
        # Top provinces
        from django.db.models import Count
        top_provinces = Patient.objects.filter(is_active=True).values('province').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return Response({
            'total_patients': total_patients,
            'active_patients': active_patients,
            'male_patients': male_patients,
            'female_patients': female_patients,
            'patients_with_insurance': patients_with_insurance,
            'top_provinces': list(top_provinces)
        })

class MedicalRecordViewSet(viewsets.ModelViewSet):
    """Medical Record management ViewSet"""
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['visit_type', 'status', 'department']
    search_fields = ['medical_record_number', 'chief_complaint']
    ordering_fields = ['visit_date', 'created_at']
    ordering = ['-visit_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MedicalRecordCreateSerializer
        return MedicalRecordSerializer
    
    def perform_create(self, serializer):
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(created_by_id=self.request.user.id, updated_by_id=self.request.user.id)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(updated_by_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List medical records",
        description="Get a list of medical records"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create medical record",
        description="Create a new medical record"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class PatientDocumentViewSet(viewsets.ModelViewSet):
    """Patient Document management ViewSet"""
    queryset = PatientDocument.objects.all()
    serializer_class = PatientDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PatientDocumentCreateSerializer
        return PatientDocumentSerializer
    
    def perform_create(self, serializer):
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(uploaded_by_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List patient documents",
        description="Get a list of patient documents"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Upload document",
        description="Upload a new patient document"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
