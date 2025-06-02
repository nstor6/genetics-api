from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import (
    RegistroUsuarioView, 
    UsuarioListView, 
    UsuarioDetailView,
    cambiar_password,
    actualizar_perfil,
    mi_perfil,
    mis_estadisticas,
    logout_view
)
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    # Autenticación
    path('register/', RegistroUsuarioView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', logout_view, name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Gestión de usuarios (admin)
    path('', UsuarioListView.as_view(), name='user-list'),
    path('<int:pk>/', UsuarioDetailView.as_view(), name='user-detail'),
    
    # Perfil del usuario autenticado
    path('mi-perfil/', mi_perfil, name='mi-perfil'),
    path('actualizar-perfil/', actualizar_perfil, name='actualizar-perfil'),
    path('change-password/', cambiar_password, name='cambiar-password'),
    path('mis-estadisticas/', mis_estadisticas, name='mis-estadisticas'),
    path('me/', mi_perfil, name='usuario-me'),
]