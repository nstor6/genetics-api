
from rest_framework.routers import DefaultRouter
from .views import AnimalViewSet

router = DefaultRouter()
router.register(r'', AnimalViewSet, basename='animal')

urlpatterns = router.urls

