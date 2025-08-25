from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'medical-records', views.MedicalRecordViewSet)
router.register(r'patient-documents', views.PatientDocumentViewSet)

urlpatterns = [
    path('validate-insurance/', views.validate_insurance, name='validate-insurance'),
    path('geo/provinces/', views.geo_provinces, name='geo_provinces_api'),
    path('geo/provinces/<int:province_code>/', views.geo_province_detail, name='geo_province_detail_api'),
    path('', include(router.urls)),
]