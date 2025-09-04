from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, VNPayTransactionViewSet, vnpay_return, vnpay_ipn

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'vnpay-transactions', VNPayTransactionViewSet, basename='vnpay-transaction')

urlpatterns = [
    path('', include(router.urls)),
    
    # VNPAY callback URLs
    path('vnpay_return/', vnpay_return, name='vnpay_return'),
    path('vnpay_ipn/', vnpay_ipn, name='vnpay_ipn'),
]
