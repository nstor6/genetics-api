from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Notificacion
from .serializers import NotificacionSerializer
from utils.permissions import IsSelfOrAdmin

class NotificacionViewSet(viewsets.ModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin':
            return Notificacion.objects.all()
        return Notificacion.objects.filter(usuario=user)

    def get_permissions(self):
        # Solo admin puede crear
        if self.request.method == 'POST':
            return [IsSelfOrAdmin()]
        return [permissions.IsAuthenticated()]
