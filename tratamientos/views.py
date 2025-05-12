from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Tratamiento
from .serializers import TratamientoSerializer
from utils.permissions import IsAdminUser

class TratamientoViewSet(viewsets.ModelViewSet):
    queryset = Tratamiento.objects.all()
    serializer_class = TratamientoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol == 'admin':
            return Tratamiento.objects.all()
        return Tratamiento.objects.filter(administrado_por=user)

    def get_permissions(self):
        # Solo admin puede crear, todos pueden ver y modificar los suyos
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
