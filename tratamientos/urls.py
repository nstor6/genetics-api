from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TratamientoViewSet

router = DefaultRouter()
router.register(r'', TratamientoViewSet, basename='tratamiento')

urlpatterns = [
    path('', include(router.urls)),
]
