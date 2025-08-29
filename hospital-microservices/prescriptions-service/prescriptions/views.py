from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import DrugCategory, Drug, Prescription, PrescriptionItem, PrescriptionDispensing
from .serializers import (
    DrugCategorySerializer, DrugSerializer, DrugCreateSerializer, DrugUpdateSerializer,
    DrugSummarySerializer, DrugInventorySerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer, PrescriptionUpdateSerializer,
    PrescriptionSummarySerializer, PrescriptionItemSerializer, PrescriptionItemCreateSerializer,
    PrescriptionDispensingSerializer, PrescriptionDispensingCreateSerializer
)

class DrugCategoryViewSet(viewsets.ModelViewSet):
    """Drug Category management ViewSet"""
    queryset = DrugCategory.objects.all()
    serializer_class = DrugCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @extend_schema(
        summary="List drug categories",
        description="Get a list of all drug categories"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class DrugViewSet(viewsets.ModelViewSet):
    """Drug management ViewSet"""
    queryset = Drug.objects.select_related('category').all()
    serializer_class = DrugSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'dosage_form', 'is_prescription_required', 'is_controlled_substance', 'is_active']
    search_fields = ['code', 'name', 'generic_name', 'brand_name', 'manufacturer']
    ordering_fields = ['name', 'unit_price', 'current_stock', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DrugCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DrugUpdateSerializer
        elif self.action == 'list':
            return DrugSummarySerializer
        return DrugSerializer
    
    @extend_schema(
        summary="List drugs",
        description="Get a list of all drugs with optional filtering"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get low stock drugs",
        description="Get drugs with current stock below minimum stock level",
        responses={200: DrugInventorySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get drugs with low stock"""
        low_stock_drugs = Drug.objects.filter(
            current_stock__lte=models.F('minimum_stock'),
            is_active=True
        ).select_related('category')
        
        serializer = DrugInventorySerializer(low_stock_drugs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get out of stock drugs",
        description="Get drugs with zero current stock",
        responses={200: DrugInventorySerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get drugs that are out of stock"""
        out_of_stock_drugs = Drug.objects.filter(
            current_stock=0,
            is_active=True
        ).select_related('category')
        
        serializer = DrugInventorySerializer(out_of_stock_drugs, many=True)
        return Response(serializer.data)

class PrescriptionViewSet(viewsets.ModelViewSet):
    """Prescription Management ViewSet"""
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'prescription_number', 'patient_id', 'doctor_id', 'diagnosis'
    ]
    filterset_fields = [
        'status', 'prescription_type', 'patient_id', 'doctor_id', 'appointment_id'
    ]
    ordering_fields = ['prescription_date', 'created_at', 'valid_until']
    ordering = ['-prescription_date']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PrescriptionUpdateSerializer
        elif self.action == 'list':
            return PrescriptionSummarySerializer
        return PrescriptionSerializer
    
    def perform_create(self, serializer):
        # Set created_by_id from request user if available
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(created_by_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List prescriptions",
        description="Get a list of all prescriptions with optional filtering"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get today's prescriptions",
        description="Get all prescriptions for today, optionally filtered by doctor",
        parameters=[
            OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
            OpenApiParameter('doctor', type=str, description='Doctor ID'),
        ],
        responses={200: PrescriptionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's prescriptions"""
        from django.utils import timezone
        from datetime import datetime
        
        date_param = request.query_params.get('date')
        doctor_param = request.query_params.get('doctor')
        
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.now().date()
        
        prescriptions = Prescription.objects.filter(
            prescription_date__date=target_date
        )
        
        if doctor_param:
            prescriptions = prescriptions.filter(doctor_id=doctor_param)
        
        serializer = PrescriptionSummarySerializer(prescriptions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get prescription statistics",
        description="Get statistics about prescriptions"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get prescription statistics"""
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        total_prescriptions = Prescription.objects.count()
        today_prescriptions = Prescription.objects.filter(
            prescription_date__date=today
        ).count()
        this_month_prescriptions = Prescription.objects.filter(
            prescription_date__gte=this_month
        ).count()
        
        # Status breakdown
        status_counts = Prescription.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Type breakdown
        type_counts = Prescription.objects.values('prescription_type').annotate(
            count=Count('id')
        ).order_by('prescription_type')
        
        # Financial summary
        financial_summary = Prescription.objects.aggregate(
            total_amount=Sum('total_amount'),
            total_insurance=Sum('insurance_covered_amount'),
            total_patient_payment=Sum('patient_payment_amount')
        )
        
        return Response({
            'total_prescriptions': total_prescriptions,
            'today_prescriptions': today_prescriptions,
            'this_month_prescriptions': this_month_prescriptions,
            'status_breakdown': list(status_counts),
            'type_breakdown': list(type_counts),
            'financial_summary': financial_summary
        })

class PrescriptionItemViewSet(viewsets.ModelViewSet):
    """Prescription Item management ViewSet"""
    queryset = PrescriptionItem.objects.select_related('prescription', 'drug').all()
    serializer_class = PrescriptionItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prescription', 'drug', 'frequency', 'route']
    search_fields = ['drug__name', 'drug__code', 'instructions']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionItemCreateSerializer
        return PrescriptionItemSerializer
    
    @extend_schema(
        summary="List prescription items",
        description="Get a list of all prescription items"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class PrescriptionDispensingViewSet(viewsets.ModelViewSet):
    """Prescription Dispensing management ViewSet"""
    queryset = PrescriptionDispensing.objects.select_related('prescription', 'prescription_item').all()
    serializer_class = PrescriptionDispensingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prescription', 'prescription_item', 'status', 'pharmacist_id']
    search_fields = ['prescription__prescription_number', 'prescription_item__drug__name']
    ordering_fields = ['dispensed_at']
    ordering = ['-dispensed_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionDispensingCreateSerializer
        return PrescriptionDispensingSerializer
    
    def perform_create(self, serializer):
        # Set pharmacist_id from request user if available
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(pharmacist_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List dispensing records",
        description="Get a list of all prescription dispensing records"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get dispensing statistics",
        description="Get statistics about prescription dispensing"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get dispensing statistics"""
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        total_dispensing = PrescriptionDispensing.objects.count()
        today_dispensing = PrescriptionDispensing.objects.filter(
            dispensed_at__date=today
        ).count()
        this_month_dispensing = PrescriptionDispensing.objects.filter(
            dispensed_at__gte=this_month
        ).count()
        
        # Status breakdown
        status_counts = PrescriptionDispensing.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Total quantity dispensed
        total_quantity = PrescriptionDispensing.objects.filter(
            status='DISPENSED'
        ).aggregate(total=Sum('quantity_dispensed'))['total'] or 0
        
        return Response({
            'total_dispensing': total_dispensing,
            'today_dispensing': today_dispensing,
            'this_month_dispensing': this_month_dispensing,
            'status_breakdown': list(status_counts),
            'total_quantity_dispensed': total_quantity
        })
