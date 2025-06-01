"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Importar después de configurar Django
django_asgi_app = get_asgi_application()

# Importar consumers
from notificaciones.consumers import NotificacionConsumer
from logs.consumers import LogConsumer
from animales.consumers import AnimalConsumer

# Rutas WebSocket
from django.urls import path

websocket_urlpatterns = [
    path('ws/notificaciones/', NotificacionConsumer.as_asgi()),
    path('ws/logs/', LogConsumer.as_asgi()),
    path('ws/animales/', AnimalConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})