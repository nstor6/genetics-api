from django.shortcuts import render
from rest_framework import viewsets
from .models import Evento
from .serializers import EventoSerializer
from utils.permissions import IsAdminUser

class EventoViewSet(viewsets.ModelViewSet):
    queryset = Evento.objects.all()
    serializer_class = EventoSerializer
    permission_classes = [IsAdminUser]  # Solo admin puede acceder
