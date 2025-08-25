from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_GET
# Import mềm để tránh sập server nếu chưa cài lib
try:
    from vietnam_provinces import NESTED_DIVISIONS_JSON_PATH as VN_PROVINCES_PATH  # type: ignore
except Exception:  # pragma: no cover
    VN_PROVINCES_PATH = None
import json as _stdlib_json

def login_view(request):
    """Login page view - No authentication required"""
    return render(request, 'auth/login.html')

def signup_view(request):
    """Signup page view - No authentication required"""
    return render(request, 'auth/signup.html')

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


# ===== Địa giới hành chính Việt Nam (local JSON via vietnam-provinces) =====

def _load_nested_divisions():
    # Load once per process (simple cache)
    # In production you can add proper caching (e.g., Django cache)
    if not hasattr(_load_nested_divisions, "_cache"):
        global VN_PROVINCES_PATH
        if VN_PROVINCES_PATH is None:
            # Thử import lại động sau khi người dùng vừa cài đặt mà không restart server
            try:
                from importlib import import_module
                VN_PROVINCES_PATH = import_module('vietnam_provinces').NESTED_DIVISIONS_JSON_PATH  # type: ignore
            except Exception:
                raise RuntimeError(
                    "vietnam-provinces chưa được cài đặt. Hãy cài gói 'vietnam-provinces'."
                )
        # Fallback chain: orjson -> rapidjson -> stdlib json
        try:
            import orjson as _orjson  # type: ignore
            _load_nested_divisions._cache = _orjson.loads(
                VN_PROVINCES_PATH.read_bytes()
            )
        except Exception:
            try:
                import rapidjson as _rapidjson  # type: ignore
                with VN_PROVINCES_PATH.open(encoding='utf-8') as f:
                    _load_nested_divisions._cache = _rapidjson.load(f)
            except Exception:
                _load_nested_divisions._cache = _stdlib_json.loads(
                    VN_PROVINCES_PATH.read_text(encoding='utf-8')
                )
    return _load_nested_divisions._cache


@require_GET
def geo_provinces(request):
    try:
        data = _load_nested_divisions()
    except Exception as exc:
        return JsonResponse({'detail': str(exc)}, status=500)
    provinces = [
        {
            'code': p['code'],
            'name': p['name'],
            'division_type': p.get('division_type')
        }
        for p in data
    ]
    return JsonResponse(provinces, safe=False)


@require_GET
def geo_province_detail(request, province_code: int):
    try:
        data = _load_nested_divisions()
    except Exception as exc:
        return JsonResponse({'detail': str(exc)}, status=500)
    for p in data:
        if int(p['code']) == int(province_code):
            # Thư viện đã gom wards trực tiếp trong province (không có cấp district)
            wards = p.get('wards', []) or p.get('districts', [])  # backward compat
            return JsonResponse({
                'code': p['code'],
                'name': p['name'],
                'wards': [
                    {
                        'code': w['code'],
                        'name': w['name'],
                    } for w in wards
                ]
            })
    return JsonResponse({'detail': 'Province not found'}, status=404)


@require_GET
def geo_district_detail(request, district_code: int):
    return JsonResponse({'detail': 'This dataset does not provide districts.'}, status=400)