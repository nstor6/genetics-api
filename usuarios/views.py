from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from .models import Usuario
from .serializers import UsuarioSerializer, RegistroUsuarioSerializer
from utils.permissions import IsAdminUser

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
            return Response(
                {"error": f"Error interno: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UsuarioListView(generics.ListAPIView):
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]  # Solo admin puede ver todos los usuarios

    def get_queryset(self):
        """Solo admins pueden ver todos los usuarios"""
        return Usuario.objects.all()

    def list(self, request, *args, **kwargs):
        try:
            print(f"👥 Listando usuarios - Usuario solicitante: {request.user} (Rol: {getattr(request.user, 'rol', 'Sin rol')})")
            
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            
            print(f"✅ Devolviendo {len(serializer.data)} usuarios")
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error listando usuarios: {e}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]  # Solo admin puede ver/editar usuarios específicos

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            print(f"👤 Obteniendo usuario: {instance.email}")
            return Response(serializer.data)
            
        except Exception as e:
            print(f"❌ Error obteniendo usuario: {e}")
            return Response(
                {"error": "Error interno del servidor"}, 
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
            return Response(
                {"error": f"Error actualizando usuario: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            email = instance.email
            
            # No permitir que un admin se elimine a sí mismo
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
            return Response(
                {"error": f"Error eliminando usuario: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Cerrar sesión del usuario
    """
    try:
        user = request.user
        print(f"🔓 Usuario cerrando sesión: {user.email}")
        
        # Aquí podrías agregar lógica adicional como:
        # - Invalidar tokens refresh
        # - Registrar en logs
        # - Limpiar sesiones activas
        
        # Registrar logout en logs
        from logs.utils import registrar_log
        registrar_log(
            usuario=user,
            tipo_accion='logout',
            entidad_afectada='session',
            entidad_id=user.id,
            observaciones='Usuario cerró sesión'
        )
        
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
        return Response(
            {"error": "Error interno del servidor"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_perfil(request):
    """
    Obtener información del perfil del usuario autenticado
    """
    try:
        user = request.user
        serializer = UsuarioSerializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error obteniendo perfil: {e}")
        return Response(
            {"error": "Error interno del servidor"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_estadisticas(request):
    """
    Obtener estadísticas del usuario autenticado
    """
    try:
        user = request.user
        
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
        
        return Response(estadisticas, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return Response(
            {"error": "Error interno del servidor"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )