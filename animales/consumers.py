import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from usuarios.models import Usuario
from .models import Animal
from .serializers import AnimalSerializer


class AnimalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Conectar usuario autenticado para updates de animales"""
        self.user = await self.get_user_from_token()
        
        if self.user and not isinstance(self.user, AnonymousUser):
            self.room_group_name = 'animal_updates'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Conectado a actualizaciones de animales'
            }))
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """Desconectar"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Manejar mensajes del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_animal':
                animal_id = data.get('animal_id')
                await self.subscribe_to_animal(animal_id)
                
            elif message_type == 'unsubscribe_animal':
                animal_id = data.get('animal_id')
                await self.unsubscribe_from_animal(animal_id)
                
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))

    async def animal_created(self, event):
        """Notificar creación de animal"""
        await self.send(text_data=json.dumps({
            'type': 'animal_created',
            'data': event['data']
        }))

    async def animal_updated(self, event):
        """Notificar actualización de animal"""
        await self.send(text_data=json.dumps({
            'type': 'animal_updated',
            'data': event['data']
        }))

    async def animal_deleted(self, event):
        """Notificar eliminación de animal"""
        await self.send(text_data=json.dumps({
            'type': 'animal_deleted',
            'data': event['data']
        }))

    async def subscribe_to_animal(self, animal_id):
        """Suscribirse a updates de un animal específico"""
        group_name = f'animal_{animal_id}'
        await self.channel_layer.group_add(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'animal_id': animal_id
        }))

    async def unsubscribe_from_animal(self, animal_id):
        """Desuscribirse de updates de un animal específico"""
        group_name = f'animal_{animal_id}'
        await self.channel_layer.group_discard(group_name, self.channel_name)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'animal_id': animal_id
        }))

    @database_sync_to_async
    def get_user_from_token(self):
        """Extraer usuario del token JWT"""
        try:
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[1].split('&')[0]
            
            if not token:
                return AnonymousUser()
            
            try:
                decoded_token = jwt.decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                if user_id:
                    return Usuario.objects.get(id=user_id)
                    
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Usuario.DoesNotExist):
                pass
                
            return AnonymousUser()
            
        except Exception as e:
            print(f"Error en autenticación WebSocket: {e}")
            return AnonymousUser()