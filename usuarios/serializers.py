from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.utils import timezone
from .models import Usuario
from django.contrib.auth import get_user_model

User = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellidos', 'email', 'rol', 'activo', 'fecha_creacion', 'ultimo_acceso']

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['nombre', 'apellidos', 'email', 'password', 'rol']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para incluir datos del usuario en el token
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar información personalizada al token
        token['nombre'] = user.nombre
        token['apellidos'] = user.apellidos
        token['email'] = user.email
        token['rol'] = user.rol
        token['activo'] = user.activo
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información del usuario a la respuesta
        data['user'] = {
            'id': self.user.id,
            'nombre': self.user.nombre,
            'apellidos': self.user.apellidos,
            'email': self.user.email,
            'rol': self.user.rol,
            'activo': self.user.activo,
            'fecha_creacion': self.user.fecha_creacion.isoformat() if self.user.fecha_creacion else None,
            'ultimo_acceso': self.user.ultimo_acceso.isoformat() if self.user.ultimo_acceso else None,
        }
        
        # Actualizar último acceso
        self.user.ultimo_acceso = timezone.now()
        self.user.save(update_fields=['ultimo_acceso'])
        
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellidos', 'email', 'rol', 'activo', 'fecha_creacion', 'ultimo_acceso']

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['nombre', 'apellidos', 'email', 'password', 'rol']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user