from logs.models import Log

def registrar_log(usuario, tipo_accion, entidad_afectada, entidad_id, cambios=None, observaciones=None):
    Log.objects.create(
        usuario=usuario,
        tipo_accion=tipo_accion,
        entidad_afectada=entidad_afectada,
        entidad_id=str(entidad_id),
        cambios=cambios,
        observaciones=observaciones
    )
