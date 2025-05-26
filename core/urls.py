from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static



schema_view = get_schema_view(
    openapi.Info(
        title="API Genetics",
        default_version='v1',
        description="Documentación interactiva de la API Genetics",
        contact=openapi.Contact(email="soporte@genetics.local"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('usuarios.urls')),
    path('api/animales/', include('animales.urls')),
    path('api/incidencias/', include('incidencias.urls')),
    path('api/tratamientos/', include('tratamientos.urls')),
    path('api/grupos/', include('grupos.urls')),
    path('api/eventos/', include('eventos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/logs/', include('logs.urls')),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

