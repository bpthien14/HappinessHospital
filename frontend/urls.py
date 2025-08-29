from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('portal/', views.patient_portal_view, name='portal'),
    # Legacy redirects to avoid 404
    path('patient-portal/', views.portal_redirect_view, name='patient_portal_legacy_dash'),
    path('patient_portal/', views.portal_redirect_view, name='patient_portal_legacy_underscore'),
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<uuid:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/<uuid:doctor_id>/', views.doctor_detail_view, name='doctor_detail'),
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('pharmacy/', views.pharmacy_inventory_view, name='pharmacy_inventory'),
    path('pharmacy/prescriptions/', views.pharmacist_prescriptions_view, name='pharmacist_prescriptions'),
    path('doctor/prescriptions/', views.doctor_prescriptions_view, name='doctor_prescriptions'),
    path('', views.dashboard_view, name='home'),  # Redirect to dashboard
    path('users/', views.user_list_view, name='user_list'),
    path('users/<uuid:user_id>/', views.user_detail_view, name='user_detail'),
]