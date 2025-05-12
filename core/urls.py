from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('usuarios.urls')),
    path('api/animales/', include('animales.urls')),
    path('api/incidencias/', include('incidencias.urls')),
    path('api/tratamientos/', include('tratamientos.urls')),
    path('api/grupos/', include('grupos.urls')),
    path('api/eventos/', include('eventos.urls')),
    path('api/notificaciones/', include('notificaciones.urls')),
    path('api/logs/', include('logs.urls')),  # <-- Añade esta línea
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
