from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def login_view(request):
    """Login page view - No authentication required"""
    return render(request, 'auth/login.html')

def dashboard_view(request):
    """Dashboard view - No authentication required, handled by frontend"""
    return render(request, 'dashboard/dashboard.html')

def patient_list_view(request):
    """Patient list view - No authentication required, handled by frontend"""
    return render(request, 'patients/patient_list.html')

def patient_detail_view(request, patient_id):
    """Patient detail view - No authentication required, handled by frontend"""
    context = {'patient_id': patient_id}
    return render(request, 'patients/patient_detail.html', context)