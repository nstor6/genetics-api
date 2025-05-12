from rest_framework import viewsets
from .models import Grupo
from .serializers import GrupoSerializer
from utils.permissions import IsAdminUser

class GrupoViewSet(viewsets.ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer
    permission_classes = [IsAdminUser]  # Solo admin puede acceder

