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
        elif self.action in ['create', 'vnpay_create', 'vnpay_qr_create', 'cash_confirm']:
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
        elif self.action in ['vnpay_create', 'vnpay_qr_create']:
            return VNPayCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        operation_id='payment_vnpay_create',
        summary='Tạo giao dịch VNPAY (redirect)',
        responses={201: PaymentSerializer, 400: OpenApiResponse(description='Không hợp lệ')}
    )
    @action(detail=False, methods=['post'])
    def vnpay_create(self, request):
        """Tạo giao dịch thanh toán VNPAY với redirect"""
        serializer = VNPayCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        prescription = serializer.validated_data['prescription']
        order_desc = serializer.validated_data['order_desc']
        amount = serializer.validated_data['amount']
        
        # Check if there's already a pending payment for this prescription
        existing_payment = Payment.objects.filter(
            prescription=prescription,
            status='PENDING'
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
        payment_url, vnp_TxnRef = vnpay_service.create_payment_url(payment, order_desc)
        
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
            'payment': PaymentSerializer(payment).data,
            'payment_url': payment_url,
            'redirect_url': payment_url
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id='payment_vnpay_qr_create',
        summary='Tạo giao dịch VNPAY với QR Code',
        responses={201: PaymentSerializer, 400: OpenApiResponse(description='Không hợp lệ')}
    )
    @action(detail=False, methods=['post'])
    def vnpay_qr_create(self, request):
        """Tạo giao dịch thanh toán VNPAY với QR Code"""
        serializer = VNPayCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        prescription = serializer.validated_data['prescription']
        order_desc = serializer.validated_data['order_desc']
        amount = serializer.validated_data['amount']
        
        # Create payment record
        payment = Payment.objects.create(
            prescription=prescription,
            method='VNPAY',
            amount=amount,
            created_by=request.user
        )
        
        # Generate VNPAY QR Code
        vnpay_service = VNPayService()
        qr_url, vnp_TxnRef = vnpay_service.create_qr_code(payment, order_desc)
        
        # Update payment with VNPAY reference and QR code
        payment.vnp_TxnRef = vnp_TxnRef
        payment.vnp_Amount = int(amount * 100)
        payment.vnp_OrderInfo = order_desc
        payment.qr_code_url = qr_url
        payment.qr_code_type = 'VNPAY_QR'
        payment.save()
        
        # Create VNPayTransaction record
        VNPayTransaction.objects.create(
            payment=payment,
            vnp_TxnRef=vnp_TxnRef,
            vnp_Amount=int(amount * 100),
            vnp_OrderInfo=order_desc,
            vnp_CreateDate=vnpay_service.get_current_timestamp(),
            vnp_IpAddr=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        
        return Response({
            'payment': PaymentSerializer(payment).data,
            'qr_code_url': qr_url,
            'qr_code_type': 'VNPAY_QR',
            'payment_id': str(payment.id)
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