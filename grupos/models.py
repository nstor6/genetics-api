from django.db import models
from animales.models import Animal

class Grupo(models.Model):
    TIPO_CHOICES = [
        ('produccion', 'Producción'),
        ('gestacion', 'Gestación'),
        ('tratamiento', 'Tratamiento'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    animal_ids = models.ManyToManyField(Animal, related_name='grupos')
    fecha_creacion = models.DateField(auto_now_add=True)
    estado_actual = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nombre

