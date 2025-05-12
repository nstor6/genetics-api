from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidenciaViewSet

router = DefaultRouter()
router.register(r'', IncidenciaViewSet, basename='incidencia')

urlpatterns = [
    path('', include(router.urls)),
]
