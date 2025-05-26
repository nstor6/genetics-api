from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Evento
from .serializers import EventoSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'animal', 'fecha_inicio', 'fecha_fin']

    def perform_create(self, serializer):
        evento = serializer.save()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='evento',
            entidad_id=evento.id,
            observaciones='Evento creado automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        anterior = EventoSerializer(original).data.copy()

        evento = serializer.save()
        nuevo = EventoSerializer(evento).data.copy()

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
            entidad_afectada='evento',
            entidad_id=evento.id,
            cambios=cambios,
            observaciones='Evento actualizado'
        )

    def perform_destroy(self, instance):
        evento_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='evento',
            entidad_id=evento_id,
            observaciones='Evento eliminado'
        )
