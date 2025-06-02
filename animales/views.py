# animales/views.py - Actualizar el método subir_imagen para usar Firebase

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from firebase_admin import storage
import uuid
import os
from datetime import datetime
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subir_imagen(self, request, pk=None):
        """
        Subir imagen de perfil para un animal a Firebase Storage
        """
        try:
            animal = self.get_object()
            
            # Verificar que se envió una imagen
            if 'image' not in request.FILES:
                return Response(
                    {'error': 'No se envió ninguna imagen'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            image_file = request.FILES['image']
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return Response(
                    {'error': 'Tipo de archivo no permitido. Use JPEG, PNG, GIF o WebP'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar tamaño (máximo 5MB)
            if image_file.size > 5 * 1024 * 1024:
                return Response(
                    {'error': 'El archivo es demasiado grande. Máximo 5MB'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generar nombre único para el archivo
            file_extension = os.path.splitext(image_file.name)[1].lower()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"animales/{animal.chapeta}_{timestamp}_{unique_id}{file_extension}"
            
            try:
                # Obtener bucket de Firebase Storage
                bucket = storage.bucket()
                
                # Eliminar imagen anterior si existe
                if animal.foto_perfil_url:
                    try:
                        # Extraer el path del archivo de la URL de Firebase
                        old_path = self.extract_firebase_path(animal.foto_perfil_url)
                        if old_path:
                            old_blob = bucket.blob(old_path)
                            if old_blob.exists():
                                old_blob.delete()
                                print(f"Imagen anterior eliminada: {old_path}")
                    except Exception as e:
                        print(f"No se pudo eliminar la imagen anterior: {e}")
                        # Continuar aunque no se pueda eliminar la imagen anterior
                
                # Subir nueva imagen
                blob = bucket.blob(file_name)
                
                # Configurar metadatos
                blob.metadata = {
                    'animal_id': str(animal.id),
                    'animal_chapeta': animal.chapeta,
                    'uploaded_by': str(request.user.id),
                    'upload_timestamp': datetime.now().isoformat()
                }
                
                # Subir archivo
                image_file.seek(0)  # Resetear puntero del archivo
                blob.upload_from_file(
                    image_file,
                    content_type=image_file.content_type
                )
                
                # Hacer el archivo público
                blob.make_public()
                
                # Obtener URL pública
                public_url = blob.public_url
                
                # Actualizar animal en la base de datos
                animal.foto_perfil_url = public_url
                animal.save()
                
                # Registrar log
                registrar_log(
                    usuario=request.user,
                    tipo_accion='actualizar_imagen',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Imagen actualizada para animal {animal.chapeta} - Firebase Storage'
                )
                
                return Response({
                    'message': 'Imagen subida exitosamente a Firebase',
                    'url': public_url,
                    'animal_id': animal.id,
                    'file_name': file_name
                }, status=status.HTTP_200_OK)
                
            except Exception as firebase_error:
                return Response(
                    {'error': f'Error al subir a Firebase Storage: {str(firebase_error)}'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Animal.DoesNotExist:
            return Response(
                {'error': 'Animal no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error interno del servidor: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def extract_firebase_path(self, firebase_url):
        """
        Extraer el path del archivo de una URL de Firebase Storage
        """
        try:
            # URL típica de Firebase: https://storage.googleapis.com/bucket-name/path/to/file
            if 'storage.googleapis.com' in firebase_url:
                # Dividir por el nombre del bucket
                parts = firebase_url.split('/')
                if len(parts) > 4:
                    # Tomar todo después del bucket name
                    bucket_index = parts.index('geneticsimg') if 'geneticsimg' in parts else -1
                    if bucket_index != -1 and bucket_index + 1 < len(parts):
                        return '/'.join(parts[bucket_index + 1:]).split('?')[0]
            
            # URL alternativa de Firebase
            elif 'firebasestorage.googleapis.com' in firebase_url:
                if '/o/' in firebase_url:
                    path_part = firebase_url.split('/o/')[1].split('?')[0]
                    # Decodificar URL encoding
                    import urllib.parse
                    return urllib.parse.unquote(path_part)
            
            return None
            
        except Exception as e:
            print(f"Error extrayendo path de Firebase: {e}")
            return None

    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def eliminar_imagen(self, request, pk=None):
        """
        Eliminar imagen de perfil del animal
        """
        try:
            animal = self.get_object()
            
            if not animal.foto_perfil_url:
                return Response(
                    {'message': 'El animal no tiene imagen de perfil'}, 
                    status=status.HTTP_200_OK
                )
            
            try:
                # Eliminar de Firebase Storage
                bucket = storage.bucket()
                file_path = self.extract_firebase_path(animal.foto_perfil_url)
                
                if file_path:
                    blob = bucket.blob(file_path)
                    if blob.exists():
                        blob.delete()
                        print(f"Imagen eliminada de Firebase: {file_path}")
                
                # Actualizar base de datos
                animal.foto_perfil_url = None
                animal.save()
                
                # Registrar log
                registrar_log(
                    usuario=request.user,
                    tipo_accion='eliminar_imagen',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Imagen eliminada para animal {animal.chapeta}'
                )
                
                return Response({
                    'message': 'Imagen eliminada exitosamente'
                }, status=status.HTTP_200_OK)
                
            except Exception as firebase_error:
                # Aunque falle eliminar de Firebase, limpiar la BD
                animal.foto_perfil_url = None
                animal.save()
                
                return Response({
                    'message': 'Referencia de imagen eliminada (posible error en Firebase)',
                    'warning': str(firebase_error)
                }, status=status.HTTP_200_OK)
                
        except Animal.DoesNotExist:
            return Response(
                {'error': 'Animal no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

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
        # Eliminar imagen de Firebase si existe
        if instance.foto_perfil_url:
            try:
                bucket = storage.bucket()
                file_path = self.extract_firebase_path(instance.foto_perfil_url)
                if file_path:
                    blob = bucket.blob(file_path)
                    if blob.exists():
                        blob.delete()
                        print(f"Imagen eliminada de Firebase al eliminar animal: {file_path}")
            except Exception as e:
                print(f"Error eliminando imagen de Firebase: {e}")
        
        animal_id = instance.id
        instance.delete()
        registrar_log(
            usuario=self.request.user,
            tipo_accion='eliminar',
            entidad_afectada='animal',
            entidad_id=animal_id,
            observaciones='Animal eliminado'
        )