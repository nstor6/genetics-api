from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
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