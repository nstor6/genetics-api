from rest_framework import viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from .models import Animal
from .serializers import AnimalSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado_productivo', 'estado_reproductivo', 'sexo', 'raza']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        animal = serializer.save(creado_por=self.request.user)
        registrar_log(
            usuario=self.request.user,
            tipo_accion='crear',
            entidad_afectada='animal',
            entidad_id=animal.id,
            cambios=None,
            observaciones='Animal creado automáticamente'
        )

    def perform_update(self, serializer):
        original = self.get_object()
        data_anterior = AnimalSerializer(original).data.copy()
        animal = serializer.save(modificado_por=self.request.user)
        data_nueva = AnimalSerializer(animal).data.copy()

        cambios = {
            campo: {
                'antes': data_anterior[campo],
                'despues': data_nueva[campo]
            }
            for campo in data_nueva
            if data_anterior[campo] != data_nueva[campo]
        }

        registrar_log(
            usuario=self.request.user,
            tipo_accion='editar',
            entidad_afectada='animal',
            entidad_id=animal.id,
            cambios=cambios,
            observaciones='Actualización de animal'
        )

    def perform_destroy(self, instance):
        animal_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='animal',
            entidad_id=animal_id,
            observaciones='Animal eliminado'
        )