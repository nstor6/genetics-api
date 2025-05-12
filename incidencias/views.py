from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Incidencia
from .serializers import IncidenciaSerializer
from utils.permissions import IsAdminUser

class IncidenciaViewSet(viewsets.ModelViewSet):
    queryset = Incidencia.objects.all()
    serializer_class = IncidenciaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Admin ve todo, usuarios solo sus propias incidencias
        user = self.request.user
        if user.rol == 'admin':
            return Incidencia.objects.all()
        return Incidencia.objects.filter(creado_por=user)
