from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# En core/urls.py - reemplazar la función health_check existente

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import redis
import firebase_admin
from datetime import datetime

def health_check(request):
    """
    Health check completo del sistema
    """
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["services"]["database"] = {
                "status": "healthy",
                "message": "Database connection OK"
            }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy", 
            "message": f"Database error: {str(e)}"
        }
        health_status["status"] = "degraded"
    
    # Check Redis (WebSockets)
    try:
        r = redis.Redis(host='localhost', port=6380, db=0)
        r.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection OK"
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
    
    # Check Firebase
    try:
        if firebase_admin._apps:
            health_status["services"]["firebase"] = {
                "status": "healthy",
                "message": "Firebase initialized"
            }
        else:
            health_status["services"]["firebase"] = {
                "status": "warning",
                "message": "Firebase not initialized"
            }
    except Exception as e:
        health_status["services"]["firebase"] = {
            "status": "unhealthy",
            "message": f"Firebase error: {str(e)}"
        }
    
    # Estadísticas básicas
    try:
        from usuarios.models import Usuario
        from animales.models import Animal
        from incidencias.models import Incidencia
        
        health_status["statistics"] = {
            "total_users": Usuario.objects.count(),
            "active_users": Usuario.objects.filter(activo=True).count(),
            "total_animals": Animal.objects.count(),
            "pending_incidents": Incidencia.objects.filter(estado='pendiente').count()
        }
    except Exception as e:
        health_status["statistics"] = {
            "error": f"Could not fetch statistics: {str(e)}"
        }
    
    # Determinar status general
    service_statuses = [service["status"] for service in health_status["services"].values()]
    if "unhealthy" in service_statuses:
        health_status["status"] = "unhealthy"
    elif "warning" in service_statuses:
        health_status["status"] = "warning"
    
    return JsonResponse(health_status)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/health/', health_check, name='health_check'),
    
    path('api/auth/', include('usuarios.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/animales/', include('animales.urls')),
    path('api/incidencias/', include('incidencias.urls')),
    path('api/tratamientos/', include('tratamientos.urls')),
    path('api/grupos/', include('grupos.urls')),
    path('api/eventos/', include('eventos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/logs/', include('logs.urls')),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)