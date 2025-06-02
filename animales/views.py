from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
import uuid
import traceback
from datetime import datetime
from .models import Animal
from .serializers import AnimalSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log

# Verificar dependencias paso a paso
print("🔍 Verificando dependencias para animales...")

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

@method_decorator(csrf_exempt, name='dispatch')
class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado_productivo', 'estado_reproductivo', 'sexo', 'raza']

    def get_permissions(self):
        """Permisos según la acción"""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]  # Cambiado temporalmente para debugging

    def list(self, request, *args, **kwargs):
        """Listar animales con manejo de errores"""
        try:
            print(f"🐄 Listando animales - Usuario: {request.user}")
            
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            print(f"✅ Devolviendo {len(serializer.data)} animales")
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error listando animales: {e}")
            traceback.print_exc()
            return Response(
                {"error": f"Error interno: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """Crear animal con logs"""
        try:
            print(f"➕ Creando animal - Datos: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                animal = serializer.save(creado_por=request.user)
                
                # Registrar en logs
                try:
                    registrar_log(
                        usuario=request.user,
                        tipo_accion='crear',
                        entidad_afectada='animal',
                        entidad_id=animal.id,
                        observaciones=f'Animal {animal.chapeta} creado'
                    )
                except Exception as log_error:
                    print(f"⚠️ Error registrando log: {log_error}")
                
                print(f"✅ Animal creado: {animal.chapeta}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error creando animal: {e}")
            traceback.print_exc()
            return Response(
                {"error": f"Error creando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Actualizar animal con logs"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            print(f"✏️ Actualizando animal: {instance.chapeta}")
            
            # Guardar datos anteriores para log
            anterior = AnimalSerializer(instance).data.copy()
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                animal = serializer.save(modificado_por=request.user)
                
                # Calcular cambios para log
                nuevo = AnimalSerializer(animal).data.copy()
                cambios = {
                    campo: {
                        'antes': anterior[campo],
                        'despues': nuevo[campo]
                    }
                    for campo in nuevo
                    if anterior.get(campo) != nuevo[campo]
                }
                
                # Registrar en logs
                try:
                    registrar_log(
                        usuario=request.user,
                        tipo_accion='editar',
                        entidad_afectada='animal',
                        entidad_id=animal.id,
                        cambios=cambios,
                        observaciones=f'Animal {animal.chapeta} actualizado'
                    )
                except Exception as log_error:
                    print(f"⚠️ Error registrando log: {log_error}")
                
                print(f"✅ Animal actualizado: {animal.chapeta}")
                return Response(serializer.data)
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error actualizando animal: {e}")
            traceback.print_exc()
            return Response(
                {"error": f"Error actualizando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Eliminar animal con logs"""
        try:
            instance = self.get_object()
            chapeta = instance.chapeta
            animal_id = instance.id
            
            print(f"🗑️ Eliminando animal: {chapeta}")
            
            # Eliminar imagen de Firebase si existe
            if instance.foto_perfil_url:
                try:
                    self.eliminar_imagen_firebase(instance.foto_perfil_url)
                except Exception as img_error:
                    print(f"⚠️ Error eliminando imagen: {img_error}")
            
            instance.delete()
            
            # Registrar en logs
            try:
                registrar_log(
                    usuario=request.user,
                    tipo_accion='eliminar',
                    entidad_afectada='animal',
                    entidad_id=animal_id,
                    observaciones=f'Animal {chapeta} eliminado'
                )
            except Exception as log_error:
                print(f"⚠️ Error registrando log: {log_error}")
            
            print(f"✅ Animal eliminado: {chapeta}")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            print(f"❌ Error eliminando animal: {e}")
            traceback.print_exc()
            return Response(
                {"error": f"Error eliminando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subir_imagen(self, request, pk=None):
        """Subir imagen de perfil del animal"""
        print("🚀 === INICIANDO SUBIDA DE IMAGEN ===")

        try:
            animal = self.get_object()
            print(f"✅ Animal encontrado: {animal.chapeta} (ID: {animal.id})")

            if 'image' not in request.FILES:
                return Response(
                    {'error': 'No se envió ninguna imagen'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            image_file = request.FILES['image']
            print(f"✅ Archivo recibido: {image_file.name}, {image_file.size} bytes, {image_file.content_type}")

            # Validaciones básicas
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if image_file.content_type not in allowed_types:
                return Response(
                    {'error': f'Tipo no permitido: {image_file.content_type}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            max_size = 10 * 1024 * 1024  # 10MB
            if image_file.size > max_size:
                return Response(
                    {'error': 'Archivo demasiado grande (máximo 10MB)'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Intentar procesar imagen
            if not PIL_AVAILABLE:
                return Response(
                    {'error': 'PIL/Pillow no está instalado'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                img = Image.open(image_file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Redimensionar si es muy grande
                if img.size[0] > 800 or img.size[1] > 800:
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                output.seek(0)
                
                print(f"✅ Imagen procesada: {len(output.getvalue())} bytes")

            except Exception as img_error:
                print(f"❌ Error procesando imagen: {img_error}")
                return Response(
                    {'error': f'Error procesando imagen: {str(img_error)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Intentar subir a Firebase
            if FIREBASE_ADMIN_AVAILABLE:
                try:
                    bucket = storage.bucket()
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_id = str(uuid.uuid4())[:8]
                    file_name = f"animales/{animal.chapeta}_{timestamp}_{unique_id}.jpg"
                    
                    blob = bucket.blob(file_name)
                    blob.upload_from_file(output, content_type='image/jpeg')
                    
                    # Hacer público
                    blob.make_public()
                    public_url = blob.public_url
                    
                    print(f"✅ Imagen subida a Firebase: {public_url}")

                except Exception as firebase_error:
                    print(f"❌ Error con Firebase: {firebase_error}")
                    return Response(
                        {'error': f'Error subiendo a Firebase: {str(firebase_error)}'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Fallback: guardar localmente
                print("⚠️ Firebase no disponible, guardando localmente")
                
                # Crear directorio si no existe
                media_dir = os.path.join('media', 'animales')
                os.makedirs(media_dir, exist_ok=True)
                
                # Generar nombre único
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_id = str(uuid.uuid4())[:8]
                file_name = f"{animal.chapeta}_{timestamp}_{unique_id}.jpg"
                file_path = os.path.join(media_dir, file_name)
                
                # Guardar archivo
                with open(file_path, 'wb') as f:
                    output.seek(0)
                    f.write(output.read())
                
                # URL pública (ajustar según tu configuración)
                public_url = f"http://localhost:8000/media/animales/{file_name}"
                print(f"✅ Imagen guardada localmente: {public_url}")

            # Actualizar animal con nueva URL
            animal.foto_perfil_url = public_url
            animal.save()

            # Registrar en logs
            try:
                registrar_log(
                    usuario=request.user,
                    tipo_accion='subir_imagen',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Imagen subida para animal {animal.chapeta}'
                )
            except Exception as log_error:
                print(f"⚠️ Error registrando log: {log_error}")

            return Response({
                'success': True, 
                'url': public_url,
                'message': 'Imagen subida correctamente'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"❌ ERROR GENERAL: {e}")
            traceback.print_exc()
            return Response(
                {'error': f'Error general: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def eliminar_imagen(self, request, pk=None):
        """Eliminar imagen de perfil del animal"""
        try:
            animal = self.get_object()
            
            if not animal.foto_perfil_url:
                return Response(
                    {'message': 'El animal no tiene imagen de perfil'}, 
                    status=status.HTTP_200_OK
                )

            # Intentar eliminar de Firebase o local
            try:
                self.eliminar_imagen_firebase(animal.foto_perfil_url)
            except Exception as img_error:
                print(f"⚠️ Error eliminando imagen: {img_error}")

            # Limpiar URL en base de datos
            animal.foto_perfil_url = None
            animal.save()

            # Registrar en logs
            try:
                registrar_log(
                    usuario=request.user,
                    tipo_accion='eliminar_imagen',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Imagen eliminada para animal {animal.chapeta}'
                )
            except Exception as log_error:
                print(f"⚠️ Error registrando log: {log_error}")

            return Response(
                {'message': 'Imagen eliminada exitosamente'}, 
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print(f"❌ Error eliminando imagen: {e}")
            traceback.print_exc()
            return Response(
                {'error': f'Error eliminando imagen: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def eliminar_imagen_firebase(self, firebase_url):
        """Método auxiliar para eliminar imagen de Firebase o local"""
        try:
            if FIREBASE_ADMIN_AVAILABLE and 'storage.googleapis.com' in firebase_url:
                # Eliminar de Firebase
                bucket = storage.bucket()
                file_path = self.extract_firebase_path(firebase_url)
                
                if file_path:
                    blob = bucket.blob(file_path)
                    if blob.exists():
                        blob.delete()
                        print(f"🗑️ Imagen eliminada de Firebase: {file_path}")
                    else:
                        print(f"⚠️ Imagen no encontrada en Firebase: {file_path}")
                        
            elif 'localhost:8000/media/' in firebase_url:
                # Eliminar archivo local
                file_path = firebase_url.replace('http://localhost:8000/media/', 'media/')
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Imagen eliminada localmente: {file_path}")
                else:
                    print(f"⚠️ Archivo local no encontrado: {file_path}")
                    
        except Exception as e:
            print(f"❌ Error eliminando imagen: {e}")

    def extract_firebase_path(self, firebase_url):
        """Extraer path de URL de Firebase"""
        try:
            if 'storage.googleapis.com' in firebase_url:
                parts = firebase_url.split('/')
                if len(parts) > 4:
                    # Buscar el índice del bucket
                    for i, part in enumerate(parts):
                        if '.appspot.com' in part or 'genetics' in part:
                            if i + 1 < len(parts):
                                return '/'.join(parts[i + 1:]).split('?')[0]
            elif 'firebasestorage.googleapis.com' in firebase_url:
                if '/o/' in firebase_url:
                    path_part = firebase_url.split('/o/')[1].split('?')[0]
                    import urllib.parse
                    return urllib.parse.unquote(path_part)
            return None
        except Exception as e:
            print(f"❌ Error extrayendo path de Firebase: {e}")
            return None