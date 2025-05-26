from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Tratamiento
from .serializers import TratamientoSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

class TratamientoViewSet(viewsets.ModelViewSet):
    queryset = Tratamiento.objects.all()
    serializer_class = TratamientoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['animal', 'fecha', 'medicamento', 'administrado_por']

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin':
            return Tratamiento.objects.all()
        return Tratamiento.objects.filter(administrado_por=user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        tratamiento = serializer.save()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='tratamiento',
            entidad_id=tratamiento.id,
            observaciones='Tratamiento creado automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        anterior = TratamientoSerializer(original).data.copy()

        tratamiento = serializer.save()
        nuevo = TratamientoSerializer(tratamiento).data.copy()

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
            entidad_afectada='tratamiento',
            entidad_id=tratamiento.id,
            cambios=cambios,
            observaciones='Tratamiento actualizado'
        )

    def perform_destroy(self, instance):
        tratamiento_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='tratamiento',
            entidad_id=tratamiento_id,
            observaciones='Tratamiento eliminado'
        )
