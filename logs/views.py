from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Log
from .serializers import LogSerializer
from utils.permissions import IsAdminUser

class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_accion', 'entidad_afectada', 'entidad_id', 'usuario', 'fecha_hora']
