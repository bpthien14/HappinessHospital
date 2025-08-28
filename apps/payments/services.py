import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings
from django.utils import timezone


class VNPayService:
    """VNPAY Payment Gateway Service"""
    
    def __init__(self):
        # VNPAY Configuration - sử dụng giá trị default cho sandbox
        self.vnp_TmnCode = getattr(settings, 'VNPAY_TMN_CODE', None) or 'DEMOV210'
        self.vnp_HashSecret = getattr(settings, 'VNPAY_HASH_SECRET', None) or 'DEMOHASHSECRET'
        self.vnp_Url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
        self.vnp_QR_Url = "https://sandbox.vnpayment.vn/paymentv2/qr"  # QR endpoint
        self.vnp_ReturnUrl = getattr(settings, 'VNPAY_RETURN_URL', None) or 'http://localhost:8000/api/payments/vnpay_return/'
        self.vnp_IpnUrl = getattr(settings, 'VNPAY_IPN_URL', None) or 'http://localhost:8000/api/payments/vnpay_ipn/'
    
    def create_payment_url(self, payment, order_desc):
        """Create VNPAY payment URL"""
        
        # Generate unique transaction reference
        vnp_TxnRef = f"DT{timezone.now().strftime('%Y%m%d%H%M%S')}{payment.id}"
        
        # Prepare payment data
        vnp_Params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.vnp_TmnCode,
            'vnp_Amount': int(payment.amount * 100),  # VNPAY requires x100
            'vnp_CurrCode': 'VND',
            'vnp_BankCode': '',  # Let user choose
            'vnp_TxnRef': vnp_TxnRef,
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.vnp_ReturnUrl,
            'vnp_IpnUrl': self.vnp_IpnUrl,
            'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
            'vnp_IpAddr': '127.0.0.1',  # Should get from request
        }
        
        # Sort parameters alphabetically
        vnp_Params = sorted(vnp_Params.items())
        
        # Create hash string
        hash_data = "&".join([f"{k}={v}" for k, v in vnp_Params])
        
        # Generate secure hash
        secureHash = hmac.new(
            self.vnp_HashSecret.encode('utf-8'),
            hash_data.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # Add secure hash to parameters
        vnp_Params.append(('vnp_SecureHash', secureHash))
        
        # Create payment URL
        payment_url = f"{self.vnp_Url}?{urllib.parse.urlencode(vnp_Params)}"
        
        return payment_url, vnp_TxnRef
    
    def verify_response(self, params):
        """Verify VNPAY response signature"""
        if not params:
            return False
            
        # Get secure hash from response
        vnp_SecureHash = params.get('vnp_SecureHash')
        if not vnp_SecureHash:
            return False
        
        # Create params without secure hash
        verify_params = {k: v for k, v in params.items() if k != 'vnp_SecureHash'}
        verify_params = sorted(verify_params.items())
        
        # Create hash string
        hash_data = "&".join([f"{k}={v}" for k, v in verify_params])
        
        # Generate expected hash
        expected_hash = hmac.new(
            self.vnp_HashSecret.encode('utf-8'),
            hash_data.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return expected_hash == vnp_SecureHash
    
    def get_response_code_description(self, code):
        """Get VNPay response code description"""
        codes = {
            '00': 'Thành công',
            '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường).',
            '09': 'Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng chưa đăng ký dịch vụ InternetBanking tại ngân hàng.',
            '10': 'Giao dịch không thành công do: Khách hàng xác thực thông tin thẻ/tài khoản không đúng quá 3 lần',
            '11': 'Giao dịch không thành công do: Đã hết hạn chờ thanh toán. Xin quý khách vui lòng thực hiện lại giao dịch.',
            '12': 'Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng bị khóa.',
            '13': 'Giao dịch không thành công do Quý khách nhập sai mật khẩu xác thực giao dịch (OTP). Xin quý khách vui lòng thực hiện lại giao dịch.',
            '24': 'Giao dịch không thành công do: Khách hàng hủy giao dịch',
            '51': 'Giao dịch không thành công do: Tài khoản của quý khách không đủ số dư để thực hiện giao dịch.',
            '65': 'Giao dịch không thành công do: Tài khoản của Quý khách đã vượt quá hạn mức giao dịch trong ngày.',
            '75': 'Ngân hàng thanh toán đang bảo trì.',
            '79': 'Giao dịch không thành công do: KH nhập sai mật khẩu thanh toán quá số lần quy định. Xin quý khách vui lòng thực hiện lại giao dịch',
            '99': 'Các lỗi khác (lỗi còn lại, không có trong danh sách mã lỗi đã liệt kê)'
        }
        return codes.get(code, f'Lỗi không xác định (mã: {code})')
    
    def create_qr_code(self, payment, order_desc):
        """Create VNPAY QR Code for mobile payment"""
        
        # Generate unique transaction reference
        vnp_TxnRef = f"DT{timezone.now().strftime('%Y%m%d%H%M%S')}{payment.id}"
        
        # QR Code parameters
        vnp_Params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.vnp_TmnCode,
            'vnp_Amount': int(payment.amount * 100),
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': vnp_TxnRef,
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.vnp_ReturnUrl,
            'vnp_IpnUrl': self.vnp_IpnUrl,
            'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%SS'),
            'vnp_IpAddr': '127.0.0.1',
            'vnp_QRCode': '1',  # Enable QR Code
            'vnp_QRCodeType': '1',  # 1: VNPAY QR, 2: VietQR
        }
        
        # Sort parameters alphabetically
        vnp_Params = sorted(vnp_Params.items())
        
        # Create hash string
        hash_data = "&".join([f"{k}={v}" for k, v in vnp_Params])
        
        # Generate secure hash
        secureHash = hmac.new(
            self.vnp_HashSecret.encode('utf-8'),
            hash_data.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        # Add secure hash to parameters
        vnp_Params.append(('vnp_SecureHash', secureHash))
        
        # Create QR Code URL
        qr_url = f"{self.vnp_QR_Url}?{urllib.parse.urlencode(vnp_Params)}"
        
        return qr_url, vnp_TxnRef
    
    def verify_response(self, response_data):
        """Verify VNPAY response signature"""
        try:
            # Remove secure hash for verification
            vnp_SecureHash = response_data.get('vnp_SecureHash', '')
            if 'vnp_SecureHash' in response_data:
                del response_data['vnp_SecureHash']
            if 'vnp_SecureHashType' in response_data:
                del response_data['vnp_SecureHashType']
            
            # Sort parameters
            vnp_Params = sorted(response_data.items())
            
            # Create hash string
            hash_data = "&".join([f"{k}={v}" for k, v in vnp_Params])
            
            # Generate hash for verification
            check_sum = hmac.new(
                self.vnp_HashSecret.encode('utf-8'),
                hash_data.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            
            return check_sum == vnp_SecureHash
            
        except Exception:
            return False
    
    def get_response_code_description(self, response_code):
        """Get human-readable description for VNPAY response codes"""
        response_codes = {
            '00': 'Giao dịch thành công',
            '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ',
            '09': 'Giao dịch không thành công do: Thẻ/Tài khoản chưa đăng ký dịch vụ InternetBanking',
            '10': 'Giao dịch không thành công do: Xác thực thông tin thẻ/tài khoản không đúng quá 3 lần',
            '11': 'Giao dịch không thành công do: Đã hết hạn chờ thanh toán',
            '12': 'Giao dịch không thành công do: Thẻ/Tài khoản của khách hàng bị khóa',
            '13': 'Giao dịch không thành công do: Nhập sai mật khẩu xác thực giao dịch (OTP)',
            '24': 'Giao dịch không thành công do: Khách hàng hủy giao dịch',
            '51': 'Giao dịch không thành công do: Tài khoản không đủ số dư',
            '65': 'Giao dịch không thành công do: Tài khoản đã vượt quá hạn mức giao dịch trong ngày',
            '75': 'Ngân hàng thanh toán đang bảo trì',
            '79': 'Giao dịch không thành công do: Nhập sai mật khẩu thanh toán quá số lần quy định',
            '99': 'Các lỗi khác',
        }
        return response_codes.get(response_code, f'Mã lỗi không xác định: {response_code}')
    
    def get_current_timestamp(self):
        """Get current timestamp in VNPAY format"""
        return timezone.now().strftime('%Y%m%d%H%M%SS')