from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegistroUsuarioView, UsuarioListView, UsuarioDetailView

urlpatterns = [
    path('register/', RegistroUsuarioView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', UsuarioListView.as_view(), name='user-list'),
    path('<int:pk>/', UsuarioDetailView.as_view(), name='user-detail'),
]
