from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'vnpay-transactions', views.VNPayTransactionViewSet, basename='vnpay-transaction')

urlpatterns = [
    path('', include(router.urls)),
    
    # VNPAY Callback URLs
    path('vnpay_return/', views.vnpay_return, name='vnpay_return'),
    path('vnpay_ipn/', views.vnpay_ipn, name='vnpay_ipn'),
]