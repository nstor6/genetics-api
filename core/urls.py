from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# Schema para Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="Genetics API",
        default_version='v1',
        description="API para gestión ganadera",
        contact=openapi.Contact(email="admin@genetics.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def health_check(request):
    """
    Health check básico y rápido
    """
    try:
        from django.db import connection
        from datetime import datetime
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    health_data = {
        "status": "ok",
        "message": "Genetics API Server is running",
        "timestamp": datetime.now().isoformat(),
        "django_version": "5.2.1",
        "database": db_status,
        "cors_enabled": True,
        "debug_mode": settings.DEBUG,
        "allowed_hosts": settings.ALLOWED_HOSTS,
    }
    
    return JsonResponse(health_data)

@csrf_exempt
@require_http_methods(["GET", "POST", "OPTIONS"])
def cors_test(request):
    """
    Endpoint específico para probar CORS
    """
    if request.method == "OPTIONS":
        response = JsonResponse({"message": "CORS preflight OK"})
    else:
        response_data = {
            "cors_test": "success",
            "method": request.method,
            "origin": request.headers.get('Origin', 'No origin header'),
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "content_type": request.headers.get('Content-Type', 'Unknown'),
            "authorization": "Present" if request.headers.get('Authorization') else "Not present",
        }
        
        if request.method == "POST" and request.body:
            try:
                body_data = json.loads(request.body)
                response_data["body_received"] = body_data
            except:
                response_data["body_received"] = "Could not parse JSON"
        
        response = JsonResponse(response_data)
    
    # Agregar headers CORS explícitamente
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response['Access-Control-Allow-Credentials'] = 'true'
    
    return response

@csrf_exempt  
def api_status(request):
    """
    Status de todos los endpoints principales
    """
    endpoints = {
        "health": "/api/health/",
        "cors_test": "/api/cors-test/", 
        "auth_login": "/api/auth/login/",
        "auth_register": "/api/auth/register/",
        "animals": "/api/animales/",
        "incidents": "/api/incidencias/",
        "treatments": "/api/tratamientos/",
        "events": "/api/eventos/",
        "notifications": "/api/notificaciones/",
        "logs": "/api/logs/",
        "swagger": "/swagger/",
    }
    
    return JsonResponse({
        "api_version": "1.0.0",
        "endpoints": endpoints,
        "server_time": "2025-06-02T12:00:00Z",
        "status": "operational"
    })

urlpatterns = [
    # Health y test endpoints
    path('api/health/', health_check, name='health_check'),
    path('api/cors-test/', cors_test, name='cors_test'),
    path('api/status/', api_status, name='api_status'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Autenticación
    path('api/auth/', include('usuarios.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # APIs principales
    path('api/animales/', include('animales.urls')),
    path('api/incidencias/', include('incidencias.urls')),
    path('api/tratamientos/', include('tratamientos.urls')),
    path('api/grupos/', include('grupos.urls')),
    path('api/eventos/', include('eventos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/logs/', include('logs.urls')),
    
    # Documentación API
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)