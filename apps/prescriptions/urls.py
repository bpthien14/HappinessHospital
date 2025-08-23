from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'drug-categories', views.DrugCategoryViewSet)
router.register(r'drugs', views.DrugViewSet)
router.register(r'prescriptions', views.PrescriptionViewSet)
router.register(r'dispensing', views.PrescriptionDispenseViewSet)

urlpatterns = [
    # Statistics endpoint
    path('prescriptions/statistics/', views.prescription_statistics, name='prescription-statistics'),
    
    # Include router URLs
    path('', include(router.urls)),
]