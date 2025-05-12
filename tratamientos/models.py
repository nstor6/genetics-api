from django.db import models
from django.conf import settings
from animales.models import Animal

class Tratamiento(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='tratamientos')
    fecha = models.DateField()
    medicamento = models.CharField(max_length=100)
    dosis = models.CharField(max_length=50)
    duracion = models.CharField(max_length=50)
    administrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicamento} - {self.animal.chapeta} ({self.fecha})"
