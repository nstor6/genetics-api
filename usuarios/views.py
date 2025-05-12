from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Usuario
from .serializers import UsuarioSerializer, RegistroUsuarioSerializer
from utils.permissions import IsAdminUser

class RegistroUsuarioView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroUsuarioSerializer
    permission_classes = []  # Registro público

class UsuarioListView(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]  # Solo admin

class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminUser]  # Solo admin
