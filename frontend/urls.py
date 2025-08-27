from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<uuid:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/<uuid:doctor_id>/', views.doctor_detail_view, name='doctor_detail'),
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    path('appointments/<uuid:appointment_id>/', views.appointment_detail_view, name='appointment_detail'),
    path('', views.dashboard_view, name='home'),  # Redirect to dashboard
]