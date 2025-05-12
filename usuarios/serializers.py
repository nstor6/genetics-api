from rest_framework import serializers
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
