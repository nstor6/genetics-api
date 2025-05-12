from django.db import models
from django.conf import settings
from animales.models import Animal

class Incidencia(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en tratamiento', 'En tratamiento'),
        ('resuelto', 'Resuelto'),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='incidencias')
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='incidencias_creadas')
    tipo = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_deteccion = models.DateField()
    reportado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='incidencias_reportadas')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_resolucion = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.animal.chapeta} ({self.estado})"

