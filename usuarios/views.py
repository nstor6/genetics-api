from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Usuario
from .serializers import UsuarioSerializer, RegistroUsuarioSerializer
from utils.permissions import IsAdminUser

@method_decorator(csrf_exempt, name='dispatch')
class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = [AllowAny]  # Permitir registro público

    def create(self, request, *args, **kwargs):
        try:
            print(f"📝 Registro de usuario - Datos: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                
                # Devolver datos del usuario creado (sin la contraseña)
                response_serializer = UsuarioSerializer(user)
                
                print(f"✅ Usuario registrado exitosamente: {user.email}")
                return Response(
                    {
                        "message": "Usuario creado exitosamente",
                        "user": response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                print(f"❌ Errores de validación en registro: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error en registro de usuario: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error interno: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class UsuarioListView(generics.ListAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Cambiado temporalmente para debugging

    def get_queryset(self):
        """Obtener usuarios según permisos"""
        user = self.request.user
        print(f"👥 Usuario solicitando lista: {user} (Rol: {getattr(user, 'rol', 'Sin rol')})")
        
        # Si es admin, puede ver todos
        if hasattr(user, 'rol') and user.rol == 'admin':
            return Usuario.objects.all()
        else:
            # Si no es admin, solo puede ver su propio perfil
            return Usuario.objects.filter(id=user.id)

    def list(self, request, *args, **kwargs):
        try:
            print(f"👥 Listando usuarios - Usuario solicitante: {request.user}")
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            print(f"✅ Devolviendo {len(serializer.data)} usuarios")
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]  # Cambiado temporalmente

    def get_object(self):
        """Obtener objeto según permisos"""
        obj = super().get_object()
        user = self.request.user
        
        # Admin puede acceder a cualquier usuario
        if hasattr(user, 'rol') and user.rol == 'admin':
            return obj
        
        # Usuario normal solo puede acceder a su propio perfil
        if obj.id != user.id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permisos para acceder a este usuario")
        
        return obj

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            print(f"👤 Obteniendo usuario: {instance.email}")
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error obteniendo usuario: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            
            print(f"✏️ Actualizando usuario: {instance.email}")
            print(f"📝 Datos recibidos: {request.data}")
            
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                user = serializer.save()
                print(f"✅ Usuario actualizado: {user.email}")
                return Response(serializer.data)
            else:
                print(f"❌ Errores de validación: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"❌ Error actualizando usuario: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error actualizando usuario: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            email = instance.email
            
            # No permitir que un usuario se elimine a sí mismo
            if instance == request.user:
                return Response(
                    {"error": "No puedes eliminarte a ti mismo"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            instance.delete()
            print(f"🗑️ Usuario eliminado: {email}")
            
            return Response(
                {"message": f"Usuario {email} eliminado exitosamente"}, 
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            print(f"❌ Error eliminando usuario: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Error eliminando usuario: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def cambiar_password(request):
    """
    Cambiar contraseña del usuario autenticado
    """
    try:
        user = request.user
        data = request.data
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {"error": "Se requieren old_password y new_password"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar contraseña actual
        if not check_password(old_password, user.password):
            return Response(
                {"error": "La contraseña actual es incorrecta"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar nueva contraseña
        if len(new_password) < 6:
            return Response(
                {"error": "La nueva contraseña debe tener al menos 6 caracteres"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cambiar contraseña
        user.set_password(new_password)
        user.save()
        
        print(f"✅ Contraseña cambiada para usuario: {user.email}")
        
        return Response(
            {"message": "Contraseña cambiada exitosamente"}, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        print(f"❌ Error cambiando contraseña: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error interno del servidor: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def logout_view(request):
    """
    Cerrar sesión del usuario
    """
    try:
        user = request.user
        print(f"🔓 Usuario cerrando sesión: {user.email}")
        
        # Registrar logout en logs
        try:
            from logs.utils import registrar_log
            registrar_log(
                usuario=user,
                tipo_accion='logout',
                entidad_afectada='session',
                entidad_id=user.id,
                observaciones='Usuario cerró sesión'
            )
        except Exception as log_error:
            print(f"⚠️ Error registrando logout en logs: {log_error}")
        
        return Response(
            {"message": "Sesión cerrada exitosamente"}, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        print(f"❌ Error en logout: {e}")
        return Response(
            {"message": "Sesión cerrada"}, 
            status=status.HTTP_200_OK
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def actualizar_perfil(request):
    """
    Actualizar perfil del usuario autenticado
    """
    try:
        user = request.user
        data = request.data
        
        print(f"✏️ Actualizando perfil de: {user.email}")
        print(f"📝 Datos recibidos: {data}")
        
        # Campos permitidos para actualizar
        campos_permitidos = ['nombre', 'apellidos', 'email']
        
        for campo in campos_permitidos:
            if campo in data:
                setattr(user, campo, data[campo])
        
        # Validar email único si se está cambiando
        if 'email' in data and data['email'] != user.email:
            if Usuario.objects.filter(email=data['email']).exists():
                return Response(
                    {"error": "Este email ya está en uso"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user.save()
        
        # Devolver datos actualizados
        serializer = UsuarioSerializer(user)
        
        print(f"✅ Perfil actualizado para: {user.email}")
        
        return Response(
            {
                "message": "Perfil actualizado exitosamente",
                "user": serializer.data
            }, 
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        print(f"❌ Error actualizando perfil: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error interno del servidor: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def mi_perfil(request):
    """
    Obtener información del perfil del usuario autenticado
    """
    try:
        user = request.user
        print(f"👤 Obteniendo perfil de: {user.email}")
        
        serializer = UsuarioSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error obteniendo perfil: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error interno del servidor: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def mis_estadisticas(request):
    """
    Obtener estadísticas del usuario autenticado
    """
    try:
        user = request.user
        print(f"📊 Obteniendo estadísticas de: {user.email}")
        
        # Estadísticas básicas por defecto
        estadisticas = {
            'animales_creados': 0,
            'incidencias_creadas': 0,
            'eventos_creados': 0,
            'tratamientos_administrados': 0,
        }
        
        try:
            # Importar modelos dinámicamente para evitar problemas de importación circular
            from animales.models import Animal
            from incidencias.models import Incidencia
            from eventos.models import Evento
            from tratamientos.models import Tratamiento
            
            estadisticas = {
                'animales_creados': Animal.objects.filter(creado_por=user).count(),
                'incidencias_creadas': Incidencia.objects.filter(creado_por=user).count(),
                'eventos_creados': Evento.objects.filter(creado_por=user).count(),
                'tratamientos_administrados': Tratamiento.objects.filter(administrado_por=user).count(),
            }
            
        except ImportError as import_error:
            print(f"⚠️ Error importando modelos: {import_error}")
            # Usar estadísticas por defecto
        except Exception as stats_error:
            print(f"⚠️ Error calculando estadísticas: {stats_error}")
            # Usar estadísticas por defecto
        
        print(f"📊 Estadísticas calculadas: {estadisticas}")
        return Response(estadisticas, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Error interno del servidor: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )