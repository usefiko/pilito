from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only for authenticated users, write for admin only"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff

