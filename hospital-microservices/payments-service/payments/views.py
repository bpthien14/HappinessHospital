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


@extend_schema(tags=['payments'])
class PaymentViewSet(ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

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
            # TODO: Implement proper permission checking with Auth Service
            from rest_framework.permissions import AllowAny
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action in ['vnpay_create']:
            return VNPayCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Get user ID from JWT token or Auth Service
            serializer.save(created_by_id=str(request.user.id) if hasattr(request.user, 'id') else None)
        else:
            serializer.save(created_by_id=None)

    @extend_schema(
        operation_id='payment_vnpay_create',
        summary='Tạo giao dịch VNPAY (redirect)',
        description='Tạo giao dịch VNPAY và trả về URL redirect để chuyển người dùng tới trang thanh toán.',
        responses={
            201: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'payment_id': {'type': 'string', 'format': 'uuid'},
                        'vnp_TxnRef': {'type': 'string'},
                        'redirect_url': {'type': 'string', 'format': 'url'}
                    }
                },
                description='URL chuyển hướng đến cổng thanh toán VNPAY'
            ),
            400: OpenApiResponse(description='Không hợp lệ')
        }
    )
    @action(detail=False, methods=['post'])
    def vnpay_create(self, request):
        """Tạo giao dịch thanh toán VNPAY với redirect"""
        serializer = VNPayCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        prescription_id = serializer.validated_data['prescription_id']
        order_desc = serializer.validated_data['order_desc']
        amount = serializer.validated_data['amount']

        # Check if there's already a paid payment for this prescription
        existing_paid = Payment.objects.filter(
            prescription_id=prescription_id,
            status='PAID'
        ).exists()

        if existing_paid:
            return Response(
                {'error': 'Đơn thuốc đã được thanh toán'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if there's already a pending payment for this prescription
        existing_payment = Payment.objects.filter(
            prescription_id=prescription_id,
            status='PENDING',
            method='VNPAY'
        ).first()

        if existing_payment:
            # Use existing payment instead of creating new one
            payment = existing_payment
        else:
            # Create new payment record
            payment = Payment.objects.create(
                prescription_id=prescription_id,
                method='VNPAY',
                amount=amount,
                created_by_id=request.user.id if request.user.is_authenticated else None
            )

        # Generate VNPAY payment URL
        vnpay_service = VNPayService()
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR', '127.0.0.1')
        payment_url, vnp_TxnRef = vnpay_service.create_payment_url(payment, order_desc, client_ip=client_ip)

        # Update payment with VNPAY reference
        payment.vnp_TxnRef = vnp_TxnRef
        payment.vnp_Amount = int(amount * 100)
        payment.vnp_OrderInfo = order_desc
        payment.save()

        # Create or get VNPayTransaction record (tránh trùng khi gọi lại)
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
            'redirect_url': payment_url,
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id='payment_cash_confirm',
        summary='Xác nhận thanh toán tiền mặt',
        description='Xác nhận thanh toán tiền mặt và tạo phiếu thu.',
        responses={
            201: OpenApiResponse(description='Phiếu thu đã được tạo'),
            400: OpenApiResponse(description='Không hợp lệ')
        }
    )
    @action(detail=True, methods=['post'])
    def cash_confirm(self, request, pk=None):
        """Xác nhận thanh toán tiền mặt"""
        payment = self.get_object()
        
        if payment.method != 'CASH':
            return Response(
                {'error': 'Chỉ có thể xác nhận thanh toán tiền mặt'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if payment.status != 'PENDING':
            return Response(
                {'error': 'Chỉ có thể xác nhận thanh toán đang chờ'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CashPaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update payment status
        payment.status = 'PAID'
        payment.save()
        
        # Create receipt
        receipt = PaymentReceipt.objects.create(
            payment=payment,
            cashier_id=request.user.id if request.user.is_authenticated else None,
            note=serializer.validated_data.get('note', '')
        )
        
        return Response({
            'message': 'Thanh toán tiền mặt đã được xác nhận',
            'receipt_number': receipt.receipt_number
        }, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id='payment_cancel',
        summary='Hủy thanh toán',
        description='Hủy thanh toán đang chờ xử lý.',
        responses={
            200: OpenApiResponse(description='Thanh toán đã được hủy'),
            400: OpenApiResponse(description='Không thể hủy thanh toán')
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Hủy thanh toán"""
        payment = self.get_object()
        
        if payment.status not in ['PENDING']:
            return Response(
                {'error': 'Chỉ có thể hủy thanh toán đang chờ xử lý'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'CANCELLED'
        payment.save()
        
        return Response({
            'message': 'Thanh toán đã được hủy'
        }, status=status.HTTP_200_OK)


@extend_schema(tags=['vnpay'])
class VNPayTransactionViewSet(ModelViewSet):
    queryset = VNPayTransaction.objects.all()
    serializer_class = VNPayTransactionSerializer
    permission_classes = []  # TODO: Add proper permissions

    @extend_schema(
        operation_id='vnpay_check_status',
        summary='Kiểm tra trạng thái giao dịch VNPAY',
        description='Kiểm tra trạng thái giao dịch VNPAY theo mã giao dịch.',
        responses={
            200: OpenApiResponse(description='Trạng thái giao dịch'),
            404: OpenApiResponse(description='Không tìm thấy giao dịch')
        }
    )
    @action(detail=False, methods=['get'])
    def check_status(self, request):
        """Kiểm tra trạng thái giao dịch VNPAY"""
        vnp_TxnRef = request.query_params.get('vnp_TxnRef')
        
        if not vnp_TxnRef:
            return Response(
                {'error': 'vnp_TxnRef is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            transaction = VNPayTransaction.objects.get(vnp_TxnRef=vnp_TxnRef)
            return Response({
                'vnp_TxnRef': transaction.vnp_TxnRef,
                'status': transaction.status,
                'payment_id': str(transaction.payment.id),
                'amount': transaction.vnp_Amount,
                'response_code': transaction.vnp_ResponseCode,
                'transaction_no': transaction.vnp_TransactionNo,
                'pay_date': transaction.vnp_PayDate,
            })
        except VNPayTransaction.DoesNotExist:
            return Response(
                {'error': 'Giao dịch không tồn tại'},
                status=status.HTTP_404_NOT_FOUND
            )


# VNPAY Callback Views
@csrf_exempt
@require_http_methods(["GET", "POST"])
def vnpay_return(request):
    """VNPAY return URL handler"""
    try:
        # Get all parameters from VNPAY
        vnp_Params = request.GET if request.method == 'GET' else request.POST
        vnp_Params = dict(vnp_Params)
        
        # Verify signature
        vnpay_service = VNPayService()
        if not vnpay_service.verify_response(vnp_Params):
            return JsonResponse({
                'error': 'Invalid signature'
            }, status=400)
        
        # Get transaction reference
        vnp_TxnRef = vnp_Params.get('vnp_TxnRef')
        vnp_ResponseCode = vnp_Params.get('vnp_ResponseCode')
        
        if not vnp_TxnRef:
            return JsonResponse({
                'error': 'Missing transaction reference'
            }, status=400)
        
        # Find the transaction
        try:
            vnpay_transaction = VNPayTransaction.objects.get(vnp_TxnRef=vnp_TxnRef)
            payment = vnpay_transaction.payment
            
            # Update transaction with response data
            vnpay_transaction.vnp_ResponseCode = vnp_ResponseCode
            vnpay_transaction.vnp_TransactionNo = vnp_Params.get('vnp_TransactionNo', '')
            vnpay_transaction.vnp_BankCode = vnp_Params.get('vnp_BankCode', '')
            vnpay_transaction.vnp_PayDate = vnp_Params.get('vnp_PayDate', '')
            vnpay_transaction.vnp_SecureHash = vnp_Params.get('vnp_SecureHash', '')
            
            # Update payment status based on response code
            if vnp_ResponseCode == '00':
                payment.status = 'PAID'
                vnpay_transaction.status = 'PAID'
                
                # Update payment with VNPAY response data
                payment.vnp_ResponseCode = vnp_ResponseCode
                payment.vnp_TransactionNo = vnp_Params.get('vnp_TransactionNo', '')
                payment.vnp_BankCode = vnp_Params.get('vnp_BankCode', '')
                payment.vnp_PayDate = vnp_Params.get('vnp_PayDate', '')
                payment.vnp_SecureHash = vnp_Params.get('vnp_SecureHash', '')
                payment.save()
                
                # TODO: Send event to Prescriptions Service to update dispensing status
                
            else:
                payment.status = 'FAILED'
                vnpay_transaction.status = 'FAILED'
            
            vnpay_transaction.save()
            
            # Redirect to frontend with result
            if vnp_ResponseCode == '00':
                redirect_url = f"/portal/?payment=success&prescription={payment.prescription_id}"
            else:
                error_message = vnpay_service.get_response_code_description(vnp_ResponseCode)
                redirect_url = f"/portal/?payment=failed&error={vnp_ResponseCode}&message={urllib.parse.quote(error_message)}"
            
            return JsonResponse({
                'status': 'success' if vnp_ResponseCode == '00' else 'failed',
                'redirect_url': redirect_url,
                'message': vnpay_service.get_response_code_description(vnp_ResponseCode)
            })
            
        except VNPayTransaction.DoesNotExist:
            return JsonResponse({
                'error': 'Transaction not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def vnpay_ipn(request):
    """VNPAY IPN (Instant Payment Notification) handler"""
    try:
        # Get all parameters from VNPAY
        vnp_Params = dict(request.POST)
        
        # Verify signature
        vnpay_service = VNPayService()
        if not vnpay_service.verify_response(vnp_Params):
            return JsonResponse({
                'RspCode': '97',
                'Message': 'Checksum failed'
            })
        
        # Get transaction reference
        vnp_TxnRef = vnp_Params.get('vnp_TxnRef')
        vnp_ResponseCode = vnp_Params.get('vnp_ResponseCode')
        
        if not vnp_TxnRef:
            return JsonResponse({
                'RspCode': '99',
                'Message': 'Missing transaction reference'
            })
        
        # Find the transaction
        try:
            vnpay_transaction = VNPayTransaction.objects.get(vnp_TxnRef=vnp_TxnRef)
            payment = vnpay_transaction.payment
            
            # Update transaction with response data
            vnpay_transaction.vnp_ResponseCode = vnp_ResponseCode
            vnpay_transaction.vnp_TransactionNo = vnp_Params.get('vnp_TransactionNo', '')
            vnpay_transaction.vnp_BankCode = vnp_Params.get('vnp_BankCode', '')
            vnpay_transaction.vnp_PayDate = vnp_Params.get('vnp_PayDate', '')
            vnpay_transaction.vnp_SecureHash = vnp_Params.get('vnp_SecureHash', '')
            
            # Update payment status based on response code
            if vnp_ResponseCode == '00':
                payment.status = 'PAID'
                vnpay_transaction.status = 'PAID'
                
                # Update payment with VNPAY response data
                payment.vnp_ResponseCode = vnp_ResponseCode
                payment.vnp_TransactionNo = vnp_Params.get('vnp_TransactionNo', '')
                payment.vnp_BankCode = vnp_Params.get('vnp_BankCode', '')
                payment.vnp_PayDate = vnp_Params.get('vnp_PayDate', '')
                payment.vnp_SecureHash = vnp_Params.get('vnp_SecureHash', '')
                payment.save()
                
                # TODO: Send event to Prescriptions Service to update dispensing status
                
            else:
                payment.status = 'FAILED'
                vnpay_transaction.status = 'FAILED'
            
            vnpay_transaction.save()
            
            return JsonResponse({
                'RspCode': '00',
                'Message': 'Success'
            })
            
        except VNPayTransaction.DoesNotExist:
            return JsonResponse({
                'RspCode': '01',
                'Message': 'Transaction not found'
            })
            
    except Exception as e:
        return JsonResponse({
            'RspCode': '99',
            'Message': 'Internal server error'
        })
