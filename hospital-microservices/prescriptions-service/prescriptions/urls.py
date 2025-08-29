from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DrugCategoryViewSet, DrugViewSet, PrescriptionViewSet,
    PrescriptionItemViewSet, PrescriptionDispensingViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'drug-categories', DrugCategoryViewSet, basename='drug-category')
router.register(r'drugs', DrugViewSet, basename='drug')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')
router.register(r'prescription-items', PrescriptionItemViewSet, basename='prescription-item')
router.register(r'dispensing', PrescriptionDispensingViewSet, basename='dispensing')

urlpatterns = [
    path('', include(router.urls)),
]
