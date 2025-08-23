from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'medical-records', views.MedicalRecordViewSet)
router.register(r'patient-documents', views.PatientDocumentViewSet)

urlpatterns = [
    # Insurance validation endpoint
    path('validate-insurance/', views.validate_insurance, name='validate-insurance'),
    
    # Include router URLs
    path('', include(router.urls)),
]