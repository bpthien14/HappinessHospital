import django_filters
from django.db.models import Q
from .models import Patient, MedicalRecord

class PatientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_name', label='Tên bệnh nhân')
    age_min = django_filters.NumberFilter(method='filter_age_min', label='Tuổi tối thiểu')
    age_max = django_filters.NumberFilter(method='filter_age_max', label='Tuổi tối đa')
    province = django_filters.CharFilter(field_name='province', lookup_expr='icontains')
    
    class Meta:
        model = Patient
        fields = {
            'gender': ['exact'],
            'has_insurance': ['exact'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_name(self, queryset, name, value):
        return queryset.filter(
            Q(full_name__icontains=value) |
            Q(patient_code__icontains=value) |
            Q(phone_number__icontains=value) |
            Q(citizen_id__icontains=value)
        )
    
    def filter_age_min(self, queryset, name, value):
        from datetime import date
        max_birth_date = date.today().replace(year=date.today().year - value)
        return queryset.filter(date_of_birth__lte=max_birth_date)
    
    def filter_age_max(self, queryset, name, value):
        from datetime import date
        min_birth_date = date.today().replace(year=date.today().year - value - 1)
        return queryset.filter(date_of_birth__gt=min_birth_date)

class MedicalRecordFilter(django_filters.FilterSet):
    visit_date_from = django_filters.DateFilter(field_name='visit_date', lookup_expr='gte')
    visit_date_to = django_filters.DateFilter(field_name='visit_date', lookup_expr='lte')
    
    class Meta:
        model = MedicalRecord
        fields = {
            'patient': ['exact'],
            'doctor': ['exact'],
            'visit_type': ['exact'],
            'status': ['exact'],
            'department': ['icontains'],
        }