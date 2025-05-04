from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Права доступа для автора либо администратора."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Разрешает чтение всем, запись — только авторизованным."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
