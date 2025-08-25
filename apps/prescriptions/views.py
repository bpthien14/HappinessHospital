from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Case, When, F
from django.utils import timezone
from datetime import date, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import (
    DrugCategory, Drug, Prescription, PrescriptionItem, 
    PrescriptionDispensing, DrugInteraction
)
from .serializers import (
    DrugCategorySerializer, DrugSerializer, DrugSearchSerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer, PrescriptionItemSerializer,
    PrescriptionDispenseSerializer, PrescriptionDispenseCreateSerializer,
    DrugInteractionSerializer, PrescriptionStatsSerializer, DrugInventorySerializer
)
from shared.permissions.base_permissions import HasPermission

@extend_schema(tags=['drugs'])
class DrugCategoryViewSet(ModelViewSet):
    """
    Drug Category Management ViewSet
    """
    queryset = DrugCategory.objects.all()
    serializer_class = DrugCategorySerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['parent', 'is_active']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PRESCRIPTION:READ']
        elif self.action == 'create':
            self.required_permissions = ['PRESCRIPTION:CREATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PRESCRIPTION:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PRESCRIPTION:DELETE']
        
        return super().get_permissions()

@extend_schema(tags=['drugs'])
class DrugViewSet(ModelViewSet):
    """
    Drug Management ViewSet
    """
    queryset = Drug.objects.select_related('category', 'created_by').all()
    serializer_class = DrugSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'generic_name', 'brand_name', 'code']
    filterset_fields = [
        'category', 'dosage_form', 'is_prescription_required', 
        'is_controlled_substance', 'is_active'
    ]
    ordering_fields = ['name', 'unit_price', 'current_stock', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PRESCRIPTION:READ']
        elif self.action == 'create':
            self.required_permissions = ['PRESCRIPTION:CREATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PRESCRIPTION:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PRESCRIPTION:DELETE']
        
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        operation_id='drug_search',
        summary='Advanced drug search',
        description='Advanced drug search with filters for name, category, and stock levels',
        parameters=[
            OpenApiParameter('q', type=str, description='Search query'),
            OpenApiParameter('category', type=str, description='Category ID'),
            OpenApiParameter('is_low_stock', type=bool, description='Filter low stock items'),
        ],
        responses={
            200: DrugSerializer,
            400: OpenApiResponse(description='Invalid search parameters'),
        }
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced drug search with filters"""
        serializer = DrugSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        # Text search
        q = serializer.validated_data.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(generic_name__icontains=q) |
                Q(brand_name__icontains=q) |
                Q(code__icontains=q)
            )
        
        # Category filter
        category = serializer.validated_data.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Stock filter
        is_low_stock = serializer.validated_data.get('is_low_stock')
        if is_low_stock is not None:
            if is_low_stock:
                queryset = queryset.filter(current_stock__lte=F('minimum_stock'))
            else:
                queryset = queryset.filter(current_stock__gt=F('minimum_stock'))
        
        # Other filters
        for field in ['dosage_form', 'is_prescription_required', 'is_active']:
            value = serializer.validated_data.get(field)
            if value is not None:
                queryset = queryset.filter(**{field: value})
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DrugSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DrugSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='drug_low_stock',
        summary='Get low stock drugs',
        description='Get drugs with current stock below minimum stock level',
        responses={
            200: DrugInventorySerializer,
        }
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get drugs with low stock levels"""
        queryset = self.get_queryset().filter(current_stock__lte=F('minimum_stock'))
        serializer = DrugInventorySerializer([
            {
                'drug_id': drug.id,
                'drug_name': drug.name,
                'current_stock': drug.current_stock,
                'minimum_stock': drug.minimum_stock,
                'status': drug.stock_status
            }
            for drug in queryset
        ], many=True)
        return Response(serializer.data)

@extend_schema(tags=['prescriptions'])
class PrescriptionViewSet(ModelViewSet):
    """
    Prescription Management ViewSet
    """
    queryset = Prescription.objects.select_related(
        'patient', 'doctor__user', 'appointment', 'created_by'
    ).prefetch_related('items__drug').all()
    serializer_class = PrescriptionSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'prescription_number', 'patient__full_name', 'patient__patient_code',
        'doctor__user__full_name'
    ]
    filterset_fields = [
        'status', 'prescription_type', 'patient', 'doctor', 'appointment'
    ]
    ordering_fields = ['prescription_date', 'created_at', 'valid_until']
    ordering = ['-prescription_date']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PRESCRIPTION:READ']
        elif self.action == 'create':
            self.required_permissions = ['PRESCRIPTION:CREATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PRESCRIPTION:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['PRESCRIPTION:DELETE']
        
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            status='ACTIVE'  # Auto-activate new prescriptions
        )
    
    @extend_schema(
        operation_id='prescription_today',
        summary='Get today\'s prescriptions',
        description='Get all prescriptions for today, optionally filtered by doctor',
        parameters=[
            OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
            OpenApiParameter('doctor', type=str, description='Doctor ID'),
        ],
        responses={
            200: PrescriptionSerializer,
        }
    )
    @action(detail=False, methods=['get'])
    def today_prescriptions(self, request):
        """Get today's prescriptions"""
        today = date.today()
        queryset = self.get_queryset().filter(prescription_date__date=today)
        
        doctor_id = request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='prescription_expiring_soon',
        summary='Get expiring prescriptions',
        description='Get prescriptions expiring in the next 7 days',
        responses={
            200: PrescriptionSerializer,
        }
    )
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get prescriptions expiring in the next 7 days"""
        seven_days_later = timezone.now() + timedelta(days=7)
        queryset = self.get_queryset().filter(
            status='ACTIVE',
            valid_until__lte=seven_days_later,
            valid_until__gt=timezone.now()
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='prescription_activate',
        summary='Activate prescription',
        description='Activate a prescription from DRAFT status to ACTIVE',
        responses={
            200: PrescriptionSerializer,
            400: OpenApiResponse(description='Prescription cannot be activated'),
        }
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a prescription"""
        prescription = self.get_object()
        
        if prescription.status != 'DRAFT':
            return Response(
                {'error': 'Chỉ có thể kích hoạt đơn thuốc ở trạng thái nháp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.status = 'ACTIVE'
        prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='prescription_cancel',
        summary='Cancel prescription',
        description='Cancel a prescription and add cancellation reason',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'reason': {
                        'type': 'string',
                        'description': 'Reason for cancellation'
                    }
                }
            }
        },
        responses={
            200: PrescriptionSerializer,
            400: OpenApiResponse(description='Prescription cannot be cancelled'),
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a prescription"""
        prescription = self.get_object()
        
        if prescription.status in ['FULLY_DISPENSED', 'CANCELLED']:
            return Response(
                {'error': 'Không thể hủy đơn thuốc đã cấp đầy đủ hoặc đã hủy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        prescription.status = 'CANCELLED'
        prescription.notes = f"{prescription.notes}\n\nĐã hủy: {reason}".strip()
        prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='prescription_check_interactions',
        summary='Check drug interactions',
        description='Check for potential drug interactions in a prescription',
        responses={
            200: OpenApiResponse(
                description='Drug interactions found',
                response={
                    'type': 'object',
                    'properties': {
                        'interactions': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/DrugInteraction'}
                        }
                    }
                }
            ),
        }
    )
    @action(detail=True, methods=['get'])
    def check_interactions(self, request, pk=None):
        """Check drug interactions in prescription"""
        prescription = self.get_object()
        drugs = [item.drug for item in prescription.items.all()]
        
        interactions = []
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # Check both directions of interaction
                interaction = DrugInteraction.objects.filter(
                    Q(drug1=drug1, drug2=drug2) | 
                    Q(drug1=drug2, drug2=drug1),
                    is_active=True
                ).first()
                
                if interaction:
                    interactions.append(DrugInteractionSerializer(interaction).data)
        
        return Response({'interactions': interactions})

@extend_schema(tags=['dispensing'])
class PrescriptionDispenseViewSet(ModelViewSet):
    """
    Prescription Dispensing ViewSet
    """
    queryset = PrescriptionDispensing.objects.select_related(
        'prescription', 'prescription_item__drug', 'pharmacist'
    ).all()
    serializer_class = PrescriptionDispenseSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'prescription', 'pharmacist']
    ordering_fields = ['dispensed_at']
    ordering = ['-dispensed_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PRESCRIPTION:READ']
        elif self.action == 'create':
            self.required_permissions = ['PRESCRIPTION:APPROVE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['PRESCRIPTION:APPROVE']
        
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionDispenseCreateSerializer
        return PrescriptionDispenseSerializer

    def create(self, request, *args, **kwargs):
        # Extra guard at view layer to ensure payment before dispensing
        prescription_item_id = request.data.get('prescription_item')
        if prescription_item_id:
            try:
                item = PrescriptionItem.objects.select_related('prescription').get(id=prescription_item_id)
                from apps.payments.models import Payment
                if not Payment.objects.filter(prescription=item.prescription, status='PAID').exists():
                    return Response({'error': 'Đơn thuốc chưa được thanh toán. Vui lòng thanh toán trước khi cấp thuốc.'}, status=status.HTTP_400_BAD_REQUEST)
            except PrescriptionItem.DoesNotExist:
                pass
            except Exception:
                # If payments app not ready, fall back to serializer validation
                pass
        return super().create(request, *args, **kwargs)

@extend_schema(
    tags=['prescriptions'],
    parameters=[
        OpenApiParameter('date_from', type=str, description='Start date YYYY-MM-DD'),
        OpenApiParameter('date_to', type=str, description='End date YYYY-MM-DD'),
        OpenApiParameter('doctor', type=str, description='Doctor ID'),
    ],
    responses={
        200: PrescriptionStatsSerializer,
        400: OpenApiResponse(description='Invalid date format'),
    }
)
@api_view(['GET'])
def prescription_statistics(request):
    """
    Prescription Statistics
    """
    
    # Date range
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    doctor_id = request.query_params.get('doctor')
    
    queryset = Prescription.objects.all()
    
    if date_from:
        try:
            date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(prescription_date__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(prescription_date__date__lte=date_to)
        except ValueError:
            pass
    
    if doctor_id:
        queryset = queryset.filter(doctor_id=doctor_id)
    
    # Calculate statistics
    stats = queryset.aggregate(
        total_prescriptions=Count('id'),
        active_prescriptions=Count(
            Case(When(status='ACTIVE', then='id'))
        ),
        expired_prescriptions=Count(
            Case(When(status='EXPIRED', then='id'))
        ),
        dispensed_prescriptions=Count(
            Case(When(status__in=['PARTIALLY_DISPENSED', 'FULLY_DISPENSED'], then='id'))
        ),
        total_amount=Sum('total_amount') or 0,
        insurance_covered=Sum('insurance_covered_amount') or 0,
    )
    
    serializer = PrescriptionStatsSerializer(stats)
    return Response(serializer.data)