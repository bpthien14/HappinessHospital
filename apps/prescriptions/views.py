from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Case, When, F
from django.utils import timezone
from datetime import date, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

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
from rest_framework.permissions import AllowAny, IsAuthenticated

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
            # Cho phép đọc công khai để portal hiển thị đơn thuốc (lọc theo patient phía client)
            self.permission_classes = [AllowAny]
            return [AllowAny()]
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
    permission_classes = [IsAuthenticated]  # Temporarily use IsAuthenticated for read access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'generic_name', 'brand_name', 'code']
    filterset_fields = [
        'category', 'dosage_form', 'is_prescription_required', 
        'is_controlled_substance', 'is_active'
    ]
    ordering_fields = ['name', 'unit_price', 'current_stock', 'created_at']
    ordering = ['name']
    
    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         self.required_permissions = ['PRESCRIPTION:READ']
    #     elif self.action == 'create':
    #         self.required_permissions = ['PRESCRIPTION:CREATE']
    #     elif self.action in ['update', 'partial_update']:
    #         self.required_permissions = ['PRESCRIPTION:UPDATE']
    #     elif self.action == 'destroy':
    #         self.required_permissions = ['PRESCRIPTION:DELETE']
    #     
    #     return super().get_permissions()
    
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
        'prescription_number', 'patient__full_name', 'patient__patient_code', 'patient__phone_number',
        'doctor__user__first_name', 'doctor__user__last_name'
    ]
    filterset_fields = [
        'status', 'prescription_type', 'patient', 'doctor', 'appointment'
    ]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Lọc theo dispensing_status nếu có
        dispensing_status = self.request.query_params.get('dispensing_status')
        if dispensing_status:
            # Lọc dựa trên trạng thái của dispensing records
            if dispensing_status == 'UNPAID':
                queryset = queryset.filter(dispensing_records__status='UNPAID').distinct()
            elif dispensing_status == 'PENDING':
                queryset = queryset.filter(dispensing_records__status='PENDING').distinct()
            elif dispensing_status == 'PREPARED':
                queryset = queryset.filter(dispensing_records__status='PREPARED').distinct()
            elif dispensing_status == 'DISPENSED':
                queryset = queryset.filter(dispensing_records__status='DISPENSED').distinct()
            elif dispensing_status == 'CANCELLED':
                queryset = queryset.filter(dispensing_records__status='CANCELLED').distinct()
        
        return queryset
    ordering_fields = ['prescription_date', 'created_at', 'valid_until']
    ordering = ['-prescription_date']
    
    
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Cho phép đọc công khai để portal hiển thị đơn thuốc (lọc theo patient phía client)
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action == 'create':
            # Temporarily use IsAuthenticated for testing
            self.permission_classes = [IsAuthenticated]
            return [IsAuthenticated()]
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
        print(f"🔍 perform_create called with user: {self.request.user}")
        print(f"🔍 Request data: {self.request.data}")
        print(f"🔍 Serializer validated data: {serializer.validated_data}")
        
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
        },
        examples=[
            OpenApiExample(
                'Activate success',
                value={
                    'id': '8a3b2b6f-1a2b-4dcd-9c6e-4d38f2a6a9b1',
                    'prescription_number': 'DT20250101000001',
                    'patient': '3e2cb3bc-6e2a-470f-9d38-1f38d6e1a111',
                    'patient_name': 'Nguyễn Văn A',
                    'patient_code': 'BN000123',
                    'patient_phone': '0900000000',
                    'doctor': '5f8c9e7a-1b2c-4d3e-8f9a-0b1c2d3e4f5a',
                    'doctor_name': 'BS. Trần B',
                    'doctor_specialization': 'Nội tổng quát',
                    'appointment': None,
                    'prescription_date': '2025-01-01T08:00:00Z',
                    'prescription_type': 'OUTPATIENT',
                    'prescription_type_display': 'Ngoại trú',
                    'status': 'ACTIVE',
                    'status_display': 'Có hiệu lực',
                    'diagnosis': 'Viêm họng cấp',
                    'notes': '',
                    'special_instructions': 'Uống sau ăn',
                    'valid_from': '2025-01-01T08:00:00Z',
                    'valid_until': '2025-01-31T08:00:00Z',
                    'is_valid': True,
                    'days_until_expiry': 20,
                    'total_amount': 150000,
                    'insurance_covered_amount': 0,
                    'patient_payment_amount': 150000,
                    'items': [],
                    'items_count': 0,
                    'created_by': '11111111-2222-3333-4444-555555555555',
                    'created_by_name': 'Điều phối viên',
                    'created_at': '2025-01-01T08:00:00Z',
                    'updated_at': '2025-01-01T08:10:00Z'
                },
                response_only=True
            ),
            OpenApiExample(
                'Activate error (not DRAFT)',
                value={
                    'error': 'Chỉ có thể kích hoạt đơn thuốc ở trạng thái nháp'
                },
                status_codes=['400'],
                response_only=True
            ),
        ]
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
        },
        examples=[
            OpenApiExample(
                'Cancel request',
                value={'reason': 'Bệnh nhân đổi phác đồ'},
                request_only=True
            ),
            OpenApiExample(
                'Cancel success',
                value={
                    'id': '8a3b2b6f-1a2b-4dcd-9c6e-4d38f2a6a9b1',
                    'status': 'CANCELLED',
                    'status_display': 'Đã hủy',
                    'notes': '\n\nĐã hủy: Bệnh nhân đổi phác đồ'
                },
                response_only=True
            ),
            OpenApiExample(
                'Cancel error (fully dispensed or already cancelled)',
                value={
                    'error': 'Không thể hủy đơn thuốc đã cấp đầy đủ hoặc đã hủy'
                },
                status_codes=['400'],
                response_only=True
            )
        ]
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
    
    @extend_schema(
        operation_id='prescription_mark_prepared',
        summary='Mark prescription as prepared',
        description='Mark prescription dispensing status as prepared',
        responses={
            200: PrescriptionSerializer,
            400: OpenApiResponse(description='Cannot mark as prepared'),
        }
    )
    @action(detail=True, methods=['post'])
    def mark_prepared(self, request, pk=None):
        """Đánh dấu đơn thuốc đã chuẩn bị"""
        prescription = self.get_object()
        
        # Cập nhật tất cả dispensing records từ PENDING sang PREPARED
        updated = prescription.dispensing_records.filter(status='PENDING').update(
            status='PREPARED',
            pharmacist=request.user,
            notes='Đã chuẩn bị thuốc'
        )
        
        if updated == 0:
            return Response(
                {'error': 'Không thể đánh dấu chuẩn bị. Đơn thuốc phải ở trạng thái chờ cấp thuốc.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='prescription_mark_dispensed',
        summary='Mark prescription as dispensed',
        description='Mark prescription dispensing status as dispensed',
        responses={
            200: PrescriptionSerializer,
            400: OpenApiResponse(description='Cannot mark as dispensed'),
        }
    )
    @action(detail=True, methods=['post'])
    def mark_dispensed(self, request, pk=None):
        """Đánh dấu đơn thuốc đã cấp phát"""
        prescription = self.get_object()
        
        # Cập nhật tất cả dispensing records từ PREPARED sang DISPENSED
        updated = prescription.dispensing_records.filter(status='PREPARED').update(
            status='DISPENSED',
            pharmacist=request.user,
            notes='Đã cấp thuốc cho bệnh nhân'
        )
        
        if updated == 0:
            return Response(
                {'error': 'Không thể đánh dấu đã cấp thuốc. Đơn thuốc phải ở trạng thái đã chuẩn bị.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cập nhật prescription status nếu tất cả đã dispensed
        all_dispensing = prescription.dispensing_records.all()
        if all(d.status == 'DISPENSED' for d in all_dispensing):
            prescription.status = 'FULLY_DISPENSED'
            prescription.save()
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

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