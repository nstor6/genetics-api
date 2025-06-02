from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Permite solo a usuarios con rol 'admin'.
    """
    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        is_admin = hasattr(request.user, 'rol') and request.user.rol == 'admin'
        
        print(f"🔐 IsAdminUser - Usuario: {request.user}")
        print(f"🔐 IsAdminUser - Autenticado: {is_authenticated}")
        print(f"🔐 IsAdminUser - Rol: {getattr(request.user, 'rol', 'Sin rol')}")
        print(f"🔐 IsAdminUser - Es Admin: {is_admin}")
        
        return is_authenticated and is_admin


class IsAdminOrUsuario(BasePermission):
    """
    Permite solo a usuarios con rol 'admin' o 'usuario'.
    """
    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        is_admin_or_user = (
            hasattr(request.user, 'rol') and 
            request.user.rol in ['admin', 'usuario']
        )
        
        print(f"🔐 IsAdminOrUsuario - Usuario: {request.user}")
        print(f"🔐 IsAdminOrUsuario - Autenticado: {is_authenticated}")
        print(f"🔐 IsAdminOrUsuario - Rol: {getattr(request.user, 'rol', 'Sin rol')}")
        print(f"🔐 IsAdminOrUsuario - Permitido: {is_admin_or_user}")
        
        return is_authenticated and is_admin_or_user


class IsSelfOrAdmin(BasePermission):
    """
    Permite al propio usuario o a un admin acceder.
    """
    def has_object_permission(self, request, view, obj):
        is_admin = hasattr(request.user, 'rol') and request.user.rol == 'admin'
        is_self = request.user == obj
        
        print(f"🔐 IsSelfOrAdmin - Usuario: {request.user}")
        print(f"🔐 IsSelfOrAdmin - Es Admin: {is_admin}")
        print(f"🔐 IsSelfOrAdmin - Es el mismo usuario: {is_self}")
        
        return is_admin or is_self


class IsAuthenticatedAndActive(BasePermission):
    """
    Permite solo a usuarios autenticados y activos.
    """
    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        is_active = hasattr(request.user, 'activo') and request.user.activo
        
        print(f"🔐 IsAuthenticatedAndActive - Usuario: {request.user}")
        print(f"🔐 IsAuthenticatedAndActive - Autenticado: {is_authenticated}")
        print(f"🔐 IsAuthenticatedAndActive - Activo: {is_active}")
        
        return is_authenticated and is_active