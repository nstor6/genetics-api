from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Permite solo a usuarios con rol 'admin'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class IsAdminOrUsuario(BasePermission):
    """
    Permite solo a usuarios con rol 'admin' o 'usuario'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ['admin', 'usuario']


class IsSelfOrAdmin(BasePermission):
    """
    Permite al propio usuario o a un admin acceder.
    """
    def has_object_permission(self, request, view, obj):
        return request.user.rol == 'admin' or request.user == obj

