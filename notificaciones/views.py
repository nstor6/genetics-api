from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Notificacion
from .serializers import NotificacionSerializer
from logs.utils import registrar_log
from utils.permissions import IsSelfOrAdmin

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'visto', 'usuario', 'relacionado_con_animal', 'relacionado_con_evento']

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin':
            return Notificacion.objects.all()
        return Notificacion.objects.filter(usuario=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSelfOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        notificacion = serializer.save()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='notificacion',
            entidad_id=notificacion.id,
            observaciones='Notificación creada automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        anterior = NotificacionSerializer(original).data.copy()

        notificacion = serializer.save()
        nuevo = NotificacionSerializer(notificacion).data.copy()

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
            entidad_afectada='notificacion',
            entidad_id=notificacion.id,
            cambios=cambios,
            observaciones='Notificación modificada'
        )

    def perform_destroy(self, instance):
        notificacion_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='notificacion',
            entidad_id=notificacion_id,
            observaciones='Notificación eliminada'
        )
