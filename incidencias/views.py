from rest_framework import viewsets, permissions
from .models import Incidencia
from .serializers import IncidenciaSerializer
from logs.utils import registrar_log

class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin':
            return Incidencia.objects.all()
        return Incidencia.objects.filter(creado_por=user)

    def perform_create(self, serializer):
        incidencia = serializer.save(creado_por=self.request.user)
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='incidencia',
            entidad_id=incidencia.id,
            observaciones='Incidencia registrada automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        anterior = IncidenciaSerializer(original).data.copy()

        incidencia = serializer.save()
        nuevo = IncidenciaSerializer(incidencia).data.copy()

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
            entidad_afectada='incidencia',
            entidad_id=incidencia.id,
            cambios=cambios,
            observaciones='Actualización de incidencia'
        )

    def perform_destroy(self, instance):
        incidencia_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='incidencia',
            entidad_id=incidencia_id,
            observaciones='Incidencia eliminada'
        )
