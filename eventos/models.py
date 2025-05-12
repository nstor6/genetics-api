from django.db import models
from django.conf import settings
from animales.models import Animal

class Evento(models.Model):
    TIPO_CHOICES = [
        ('visita', 'Visita veterinaria'),
        ('tratamiento', 'Tratamiento'),
        ('alerta_parto', 'Alerta de parto'),
        ('otro', 'Otro'),
    ]

    recurrente = models.BooleanField(default=False)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name='eventos')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.titulo

