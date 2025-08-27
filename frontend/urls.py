from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<uuid:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<uuid:user_id>/', views.user_detail_view, name='user_detail'),
]