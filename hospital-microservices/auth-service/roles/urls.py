from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PermissionViewSet, RoleViewSet, RolePermissionViewSet, UserRoleViewSet
)

router = DefaultRouter()
router.register(r'permissions', PermissionViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'role-permissions', RolePermissionViewSet)
router.register(r'user-roles', UserRoleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
