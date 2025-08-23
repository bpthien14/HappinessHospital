from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def login_view(request):
    """Login page view"""
    return render(request, 'auth/login.html')

@login_required
def dashboard_view(request):
    """Dashboard view"""
    return render(request, 'dashboard/dashboard.html')

@login_required
def patient_list_view(request):
    """Patient list view"""
    return render(request, 'patients/patient_list.html')

@login_required
def patient_detail_view(request, patient_id):
    """Patient detail view"""
    context = {'patient_id': patient_id}
    return render(request, 'patients/patient_detail.html', context)