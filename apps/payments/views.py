from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import urllib.parse

from .models import Payment, PaymentReceipt, VNPayTransaction
from .serializers import (
    PaymentSerializer, PaymentCreateSerializer, VNPayCreateSerializer,
    CashPaymentConfirmSerializer, PaymentReceiptSerializer, VNPayTransactionSerializer
)
from .services import VNPayService
from shared.permissions.base_permissions import HasPermission


@extend_schema(tags=['payments'])
class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.select_related('prescription', 'created_by').all()
    serializer_class = PaymentSerializer
    permission_classes = [HasPermission]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Allow patients to view their own payments for portal access
            from rest_framework.permissions import AllowAny
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action in ['create', 'vnpay_create', 'cash_confirm']:
            # Allow patients to create payments for their prescriptions
            from rest_framework.permissions import AllowAny
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'cancel']:
            self.required_permissions = ['PAYMENT:UPDATE']
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['vnpay_create']:
            return VNPayCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        operation_id='payment_vnpay_create',
        summary='Tạo giao dịch VNPAY (redirect)',
        description='Tạo giao dịch VNPAY và trả về URL redirect để chuyển người dùng tới trang thanh toán.',
        responses={
            201: OpenApiResponse(description='{"payment_id":"UUID","vnp_TxnRef":"string","redirect_url":"url"}'),
            400: OpenApiResponse(description='Không hợp lệ')
        }
    )
    @action(detail=False, methods=['post'])
    def vnpay_create(self, request):
        """Tạo giao dịch thanh toán VNPAY với redirect"""
        serializer = VNPayCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        prescription = serializer.validated_data['prescription']
        order_desc = serializer.validated_data['order_desc']
        amount = serializer.validated_data['amount']
        
        # Check if there's already a payment for this prescription
        existing_paid = Payment.objects.filter(
            prescription=prescription,
            status='PAID'
        ).exists()
        
        if existing_paid:
            return Response(
                {'error': 'Đơn thuốc đã được thanh toán'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's already a pending payment for this prescription
        existing_payment = Payment.objects.filter(
            prescription=prescription,
            status='PENDING',
            method='VNPAY'
        ).first()
        
        if existing_payment:
            # Use existing payment instead of creating new one
            payment = existing_payment
        else:
            # Create new payment record
            payment = Payment.objects.create(
                prescription=prescription,
                method='VNPAY',
                amount=amount,
                created_by=request.user
            )
        
        # Generate VNPAY payment URL
        vnpay_service = VNPayService()
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR', '127.0.0.1')
        payment_url, vnp_TxnRef = vnpay_service.create_payment_url(payment, order_desc, client_ip=client_ip)
        
        # Update payment with VNPAY reference
        payment.vnp_TxnRef = vnp_TxnRef
        payment.vnp_Amount = int(amount * 100)
        payment.vnp_OrderInfo = order_desc
        payment.qr_code_type = 'VNPAY_REDIRECT'
        payment.save()
        
        # Create or get VNPayTransaction record (avoid duplicate)
        vnpay_transaction, created = VNPayTransaction.objects.get_or_create(
            payment=payment,
            defaults={
                'vnp_TxnRef': vnp_TxnRef,
                'vnp_Amount': int(amount * 100),
                'vnp_OrderInfo': order_desc,
                'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
                'vnp_IpAddr': request.META.get('REMOTE_ADDR', '127.0.0.1')
            }
        )
        
        return Response({
            'payment_id': str(payment.id),
            'vnp_TxnRef': vnp_TxnRef,
            'redirect_url': payment_url
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id='payment_cash_confirm',
        summary='Xác nhận thanh toán tiền mặt và phát hành phiếu thu',
        request=CashPaymentConfirmSerializer,
        responses={200: PaymentReceiptSerializer, 400: OpenApiResponse(description='Không hợp lệ')}
    )
    @action(detail=True, methods=['post'])
    def cash_confirm(self, request, pk=None):
        """Xác nhận thanh toán tiền mặt"""
        payment = self.get_object()
        if payment.method != 'CASH':
            return Response({'error': 'Chỉ áp dụng cho thanh toán tiền mặt'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.status == 'PAID':
            return Response({'error': 'Thanh toán đã được xác nhận'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CashPaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.status = 'PAID'
        payment.save()

        receipt = PaymentReceipt.objects.create(
            payment=payment, 
            cashier=request.user, 
            note=serializer.validated_data.get('note', '')
        )
        return Response(PaymentReceiptSerializer(receipt).data)

    @extend_schema(
        operation_id='payment_cancel',
        summary='Hủy thanh toán',
        responses={200: PaymentSerializer}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Hủy thanh toán"""
        payment = self.get_object()
        if payment.status == 'PAID':
            return Response({'error': 'Không thể hủy giao dịch đã thanh toán'}, status=status.HTTP_400_BAD_REQUEST)
        payment.status = 'CANCELLED'
        payment.save()
        return Response(PaymentSerializer(payment).data)
    
    @extend_schema(
        operation_id='payment_by_prescription',
        summary='Lấy thanh toán theo đơn thuốc',
        description='Lấy tất cả thanh toán cho một đơn thuốc cụ thể (dành cho portal)',
        responses={200: PaymentSerializer}
    )
    @action(detail=False, methods=['get'])
    def by_prescription(self, request):
        """Lấy thanh toán theo đơn thuốc"""
        prescription_id = request.query_params.get('prescription_id')
        if not prescription_id:
            return Response(
                {'error': 'prescription_id là bắt buộc'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payments = self.get_queryset().filter(prescription_id=prescription_id)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id='payment_check_status',
        summary='Kiểm tra trạng thái thanh toán VNPAY',
        description='Kiểm tra trạng thái thanh toán VNPAY theo vnp_TxnRef',
        responses={200: PaymentSerializer}
    )
    @action(detail=False, methods=['get'])
    def check_vnpay_status(self, request):
        """Kiểm tra trạng thái thanh toán VNPAY"""
        vnp_txn_ref = request.query_params.get('vnp_TxnRef')
        if not vnp_txn_ref:
            return Response(
                {'error': 'vnp_TxnRef là bắt buộc'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payment = Payment.objects.get(vnp_TxnRef=vnp_txn_ref, method='VNPAY')
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Không tìm thấy giao dịch VNPAY'}, 
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(tags=['vnpay'])
class VNPayTransactionViewSet(ModelViewSet):
    """VNPAY Transaction Management"""
    queryset = VNPayTransaction.objects.select_related('payment__prescription').all()
    serializer_class = VNPayTransactionSerializer
    permission_classes = [HasPermission]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['PAYMENT:READ']
        return super().get_permissions()


# VNPAY Callback Views
@csrf_exempt
@require_http_methods(["GET"])
def vnpay_return(request):
    """VNPAY Return URL - User returns from VNPAY"""
    vnpay_service = VNPayService()
    
    # Verify response signature
    if not vnpay_service.verify_response(request.GET):
        return JsonResponse({'error': 'Chữ ký không hợp lệ'}, status=400)
    
    # Process response
    vnp_ResponseCode = request.GET.get('vnp_ResponseCode')
    vnp_TxnRef = request.GET.get('vnp_TxnRef')
    vnp_TransactionNo = request.GET.get('vnp_TransactionNo')
    vnp_Amount = request.GET.get('vnp_Amount')
    vnp_BankCode = request.GET.get('vnp_BankCode')
    vnp_PayDate = request.GET.get('vnp_PayDate')
    
    try:
        # Find payment by VNPAY reference
        payment = Payment.objects.get(vnp_TxnRef=vnp_TxnRef, method='VNPAY')
        
        if vnp_ResponseCode == '00':  # Success
            payment.status = 'PAID'
            payment.vnp_ResponseCode = vnp_ResponseCode
            payment.vnp_TransactionNo = vnp_TransactionNo
            payment.vnp_BankCode = vnp_BankCode
            payment.vnp_PayDate = vnp_PayDate
            payment.save()
            
            # Update VNPayTransaction
            try:
                vnpay_transaction = VNPayTransaction.objects.get(payment=payment)
                vnpay_transaction.vnp_ResponseCode = vnp_ResponseCode
                vnpay_transaction.vnp_TransactionNo = vnp_TransactionNo
                vnpay_transaction.vnp_BankCode = vnp_BankCode
                vnpay_transaction.vnp_PayDate = vnp_PayDate
                vnpay_transaction.save()
            except VNPayTransaction.DoesNotExist:
                pass  # Transaction record may not exist
            
            # Redirect to success page in portal
            from django.shortcuts import redirect
            return redirect(f'/portal/?payment=success&prescription={payment.prescription.prescription_number}')
        else:
            # Payment failed
            payment.status = 'FAILED'
            payment.vnp_ResponseCode = vnp_ResponseCode
            payment.save()
            
            error_desc = vnpay_service.get_response_code_description(vnp_ResponseCode)
            # Redirect to failure page in portal
            return redirect(f'/portal/?payment=failed&error={vnp_ResponseCode}&message={urllib.parse.quote(error_desc)}')
            
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Giao dịch không tồn tại'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Lỗi xử lý: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vnpay_ipn(request):
    """VNPAY IPN (Instant Payment Notification)"""
    vnpay_service = VNPayService()
    
    # Verify IPN signature
    if not vnpay_service.verify_response(request.POST):
        return JsonResponse({'error': 'Chữ ký IPN không hợp lệ'}, status=400)
    
    # Process IPN data (similar to return URL but for server-to-server)
    # This ensures payment status is updated even if user doesn't return to site
    
    return JsonResponse({'status': 'success'})