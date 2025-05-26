from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.core.files.uploadedfile import InMemoryUploadedFile
from core import firebase
from firebase_admin import storage
import uuid

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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
        url_path='subir-imagen'
    )
    def subir_imagen(self, request, pk=None):
        try:
            animal = self.get_object()
        except Animal.DoesNotExist:
            return Response({'error': 'Animal no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        image: InMemoryUploadedFile = request.FILES.get('image')
        if not image:
            return Response({'error': 'No se proporcionó una imagen'}, status=status.HTTP_400_BAD_REQUEST)

        extension = image.name.split('.')[-1]
        filename = f"animales/{pk}/foto_{uuid.uuid4()}.{extension}"

        bucket = storage.bucket('geneticsimg')  # bucket personalizado
        blob = bucket.blob(filename)
        blob.upload_from_file(image.file, content_type=image.content_type)

        url = f"https://storage.googleapis.com/{bucket.name}/{filename}"

        old_url = animal.foto_perfil_url
        animal.foto_perfil_url = url
        animal.save()

        registrar_log(
            usuario=request.user,
            tipo_accion='editar',
            entidad_afectada='animal',
            entidad_id=animal.id,
            cambios={'foto_perfil_url': {'antes': old_url, 'despues': url}},
            observaciones='Imagen subida a bucket geneticsimg'
        )

        return Response({'message': 'Imagen subida correctamente', 'url': url}, status=status.HTTP_200_OK)
