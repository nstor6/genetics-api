from django.shortcuts import render
from rest_framework import viewsets
from .models import Log
from .serializers import LogSerializer
from utils.permissions import IsAdminUser

class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAdminUser]  # Solo admin puede acceder
