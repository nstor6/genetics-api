from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import os
import uuid
import traceback
from datetime import datetime
from .models import Animal
from .serializers import AnimalSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

# Verificar dependencias paso a paso
print("🔍 Verificando dependencias...")

# 1. PIL/Pillow
try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
    print("✅ PIL/Pillow disponible")
except ImportError as e:
    PIL_AVAILABLE = False
    print(f"❌ PIL/Pillow no disponible: {e}")

# 2. Firebase
try:
    from firebase_admin import storage
    import firebase_admin
    FIREBASE_ADMIN_AVAILABLE = True
    print("✅ firebase_admin disponible")
except ImportError as e:
    FIREBASE_ADMIN_AVAILABLE = False
    print(f"❌ firebase_admin no disponible: {e}")

# 3. Firebase personalizado
try:
    from core.firebase import get_storage_bucket
    FIREBASE_CUSTOM_AVAILABLE = True
    print("✅ core.firebase disponible")
except ImportError as e:
    FIREBASE_CUSTOM_AVAILABLE = False
    print(f"❌ core.firebase no disponible: {e}")

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
        print("🚀 === INICIANDO SUBIDA REAL DE IMAGEN ===")

        try:
            animal = self.get_object()
            print(f"✅ Animal encontrado: {animal.chapeta} (ID: {animal.id})")

            if 'image' not in request.FILES:
                return Response({'error': 'No se envió ninguna imagen'}, status=status.HTTP_400_BAD_REQUEST)

            image_file = request.FILES['image']
            print(f"✅ Archivo recibido: {image_file.name}, {image_file.size} bytes, {image_file.content_type}")

            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return Response({'error': f'Tipo no permitido: {image_file.content_type}'}, status=status.HTTP_400_BAD_REQUEST)

            max_size = 10 * 1024 * 1024
            if image_file.size > max_size:
                return Response({'error': 'Archivo demasiado grande'}, status=status.HTTP_400_BAD_REQUEST)

            img = Image.open(image_file)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)

            if FIREBASE_CUSTOM_AVAILABLE:
                bucket = get_storage_bucket()
            elif FIREBASE_ADMIN_AVAILABLE:
                bucket = storage.bucket()
            else:
                return Response({'error': 'Firebase no configurado'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"animales/{animal.chapeta}_{timestamp}_{unique_id}.jpg"
            blob = bucket.blob(file_name)
            blob.upload_from_file(output, content_type='image/jpeg')
            public_url = f"https://storage.googleapis.com/{bucket.name}/{file_name}"


            animal.foto_perfil_url = public_url
            animal.save()

            return Response({'success': True, 'url': public_url}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return Response({'error': f'Error general: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser])
    def eliminar_imagen(self, request, pk=None):
        try:
            animal = self.get_object()

            if not animal.foto_perfil_url:
                return Response({'message': 'El animal no tiene imagen de perfil'}, status=status.HTTP_200_OK)

            try:
                bucket = storage.bucket()
                file_path = self.extract_firebase_path(animal.foto_perfil_url)

                if file_path:
                    blob = bucket.blob(file_path)
                    if blob.exists():
                        blob.delete()
                        print(f"Imagen eliminada de Firebase: {file_path}")

                animal.foto_perfil_url = None
                animal.save()

                registrar_log(
                    usuario=request.user,
                    tipo_accion='eliminar_imagen',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Imagen eliminada para animal {animal.chapeta}'
                )

                return Response({'message': 'Imagen eliminada exitosamente'}, status=status.HTTP_200_OK)

            except Exception as firebase_error:
                animal.foto_perfil_url = None
                animal.save()

                return Response({
                    'message': 'Referencia de imagen eliminada (posible error en Firebase)',
                    'warning': str(firebase_error)
                }, status=status.HTTP_200_OK)

        except Animal.DoesNotExist:
            return Response({'error': 'Animal no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def extract_firebase_path(self, firebase_url):
        try:
            if 'storage.googleapis.com' in firebase_url:
                parts = firebase_url.split('/')
                if len(parts) > 4:
                    bucket_index = parts.index('geneticsimg') if 'geneticsimg' in parts else -1
                    if bucket_index != -1 and bucket_index + 1 < len(parts):
                        return '/'.join(parts[bucket_index + 1:]).split('?')[0]
            elif 'firebasestorage.googleapis.com' in firebase_url:
                if '/o/' in firebase_url:
                    path_part = firebase_url.split('/o/')[1].split('?')[0]
                    import urllib.parse
                    return urllib.parse.unquote(path_part)
            return None
        except Exception as e:
            print(f"Error extrayendo path de Firebase: {e}")
            return None

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
