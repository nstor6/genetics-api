from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Animal
from .serializers import AnimalSerializer
from utils.permissions import IsAdminUser
from logs.utils import registrar_log
from core.firebase_storage import firebase_storage

class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['estado_productivo', 'estado_reproductivo', 'sexo', 'raza']

    def get_permissions(self):
        """Permisos: usuarios autenticados pueden hacer operaciones"""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        """Listar animales"""
        try:
            print(f"🐄 Usuario: {request.user} (Rol: {getattr(request.user, 'rol', 'No definido')})")
            queryset = self.filter_queryset(self.get_queryset())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            print(f"✅ Devolviendo {len(serializer.data)} animales")
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Error en list de animales: {e}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """Crear animal"""
        try:
            print(f"🐄 Creando animal - Usuario: {request.user}")
            print(f"📝 Datos recibidos: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                animal = serializer.save(creado_por=request.user)
                
                # Registrar log
                registrar_log(
                    usuario=request.user,
                    tipo_accion='crear',
                    entidad_afectada='animal',
                    entidad_id=animal.id,
                    observaciones=f'Animal {animal.chapeta} creado'
                )
                
                print(f"✅ Animal creado exitosamente: {animal.chapeta}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error creando animal: {e}")
            return Response(
                {"error": f"Error creando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """Actualizar animal"""
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            # Guardar datos anteriores para el log
            datos_anteriores = AnimalSerializer(instance).data.copy()
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                animal = serializer.save(modificado_por=request.user)
                
                # Calcular cambios para el log
                datos_nuevos = AnimalSerializer(animal).data.copy()
                cambios = {
                    campo: {
                        'antes': datos_anteriores[campo],
                        'despues': datos_nuevos[campo]
                    }
                    for campo in datos_nuevos
                    if datos_anteriores.get(campo) != datos_nuevos[campo]
                }
                
                # Registrar log solo si hay cambios
                if cambios:
                    registrar_log(
                        usuario=request.user,
                        tipo_accion='editar',
                        entidad_afectada='animal',
                        entidad_id=animal.id,
                        cambios=cambios,
                        observaciones=f'Animal {animal.chapeta} actualizado'
                    )
                
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error actualizando animal: {e}")
            return Response(
                {"error": f"Error actualizando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Eliminar animal"""
        try:
            instance = self.get_object()
            animal_id = instance.id
            chapeta = instance.chapeta
            
            # Eliminar foto de Firebase si existe
            if instance.foto_perfil_url:
                try:
                    storage_path = firebase_storage.extract_storage_path_from_url(instance.foto_perfil_url)
                    if storage_path:
                        firebase_storage.delete_image(storage_path)
                        print(f"🗑️ Foto eliminada de Firebase: {storage_path}")
                except Exception as e:
                    print(f"⚠️ Error eliminando foto de Firebase: {e}")
            
            instance.delete()
            
            # Registrar log
            registrar_log(
                usuario=request.user,
                tipo_accion='eliminar',
                entidad_afectada='animal',
                entidad_id=animal_id,
                observaciones=f'Animal {chapeta} eliminado'
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            print(f"❌ Error eliminando animal: {e}")
            return Response(
                {"error": f"Error eliminando animal: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def subir_imagen(self, request, pk=None):
        """
        Endpoint para subir imagen a Firebase Storage
        URL: /api/animales/{id}/subir_imagen/
        """
        try:
            animal = self.get_object()
            
            # Verificar que se envió una imagen
            if 'image' not in request.FILES:
                return Response(
                    {'error': 'No se encontró ninguna imagen en la petición'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            image_file = request.FILES['image']
            
            print(f"📷 Iniciando upload para animal {animal.chapeta}")
            print(f"📄 Archivo: {image_file.name} ({image_file.size} bytes)")
            print(f"📄 Content-Type: {image_file.content_type}")
            
            # Eliminar imagen anterior si existe
            if animal.foto_perfil_url:
                try:
                    old_storage_path = firebase_storage.extract_storage_path_from_url(animal.foto_perfil_url)
                    if old_storage_path:
                        firebase_storage.delete_image(old_storage_path)
                        print(f"🗑️ Imagen anterior eliminada: {old_storage_path}")
                except Exception as e:
                    print(f"⚠️ Error eliminando imagen anterior: {e}")
            
            # Subir nueva imagen a Firebase
            upload_result = firebase_storage.upload_image(
                image_file=image_file,
                entity_type='animales',
                entity_id=animal.id
            )
            
            if 'error' in upload_result:
                print(f"❌ Error en upload: {upload_result['error']}")
                return Response(
                    {'error': upload_result['error']}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Actualizar URL en el modelo
            new_url = upload_result['url']
            animal.foto_perfil_url = new_url
            animal.save()
            
            # Registrar log
            registrar_log(
                usuario=request.user,
                tipo_accion='editar',
                entidad_afectada='animal',
                entidad_id=animal.id,
                observaciones=f'Imagen actualizada para animal {animal.chapeta}'
            )
            
            print(f"✅ Upload completado exitosamente:")
            print(f"   URL: {new_url}")
            print(f"   Storage path: {upload_result.get('storage_path')}")
            
            return Response({
                'success': True,
                'url': new_url,
                'storage_path': upload_result.get('storage_path'),
                'message': 'Imagen subida correctamente a Firebase Storage'
            })
            
        except Exception as e:
            print(f"❌ Error en subir_imagen: {e}")
            import traceback
            traceback.print_exc()
            
            return Response(
                {'error': f'Error interno: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )