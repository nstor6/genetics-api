from rest_framework import viewsets, permissions
from .models import Animal
from .serializers import AnimalSerializer
from utils.permissions import IsAdminUser

class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer

    def get_permissions(self):
        # Solo admin puede modificar, todos pueden leer
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]

