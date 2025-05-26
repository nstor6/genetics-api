from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Grupo
from .serializers import GrupoSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

class GrupoViewSet(viewsets.ModelViewSet):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'estado_actual', 'fecha_creacion']
    
    def perform_create(self, serializer):
        grupo = serializer.save()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='grupo',
            entidad_id=grupo.id,
            observaciones='Grupo creado automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        anterior = GrupoSerializer(original).data.copy()

        grupo = serializer.save()
        nuevo = GrupoSerializer(grupo).data.copy()

        cambios = {
            campo: {
                'antes': anterior[campo],
                'despues': nuevo[campo]
            }
            for campo in nuevo
            if anterior[campo] != nuevo[campo]
        }

        registrar_log(
            usuario=self.request.user,
            tipo_accion='editar',
            entidad_afectada='grupo',
            entidad_id=grupo.id,
            cambios=cambios,
            observaciones='Grupo modificado'
        )

    def perform_destroy(self, instance):
        grupo_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='grupo',
            entidad_id=grupo_id,
            observaciones='Grupo eliminado'
        )
