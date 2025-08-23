from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<uuid:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('', views.dashboard_view, name='home'),  # Redirect to dashboard
]