import os
import uuid
import json
from django.conf import settings
import firebase_admin
from firebase_admin import credentials, storage
from PIL import Image
import io
import requests

class FirebaseStorageService:
    """Servicio para manejar uploads a Firebase Storage"""
    
    def __init__(self):
        self.bucket_name = 'genetics-426ea.appspot.com'  # Formato correcto
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Inicializar Firebase si no está inicializado"""
        if not firebase_admin._apps:
            try:
                # Buscar el archivo de credenciales en diferentes ubicaciones
                possible_paths = [
                    os.path.join(settings.BASE_DIR, 'core', 'genetics-426ea-firebase-adminsdk-fbsvc-4756c53f8c.json'),
                    os.path.join(settings.BASE_DIR, 'genetics-426ea-firebase-adminsdk-fbsvc-4756c53f8c.json'),
                    os.path.join(os.path.dirname(__file__), 'genetics-426ea-firebase-adminsdk-fbsvc-4756c53f8c.json'),
                ]
                
                cred_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        cred_path = path
                        break
                
                if not cred_path:
                    print(f"⚠️ Archivo de credenciales Firebase no encontrado en:")
                    for path in possible_paths:
                        print(f"   - {path}")
                    return False
                
                print(f"✅ Usando credenciales Firebase: {cred_path}")
                
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': self.bucket_name
                })
                print("✅ Firebase inicializado correctamente")
                return True
                
            except Exception as e:
                print(f"❌ Error inicializando Firebase: {e}")
                return False
        return True
    
    def upload_image(self, image_file, entity_type, entity_id):
        """
        Subir imagen a Firebase Storage con permisos públicos
        
        Args:
            image_file: Archivo de imagen
            entity_type: Tipo de entidad (ej: 'animales')
            entity_id: ID de la entidad
            
        Returns:
            dict: URL pública de la imagen o error
        """
        try:
            if not self.initialize_firebase():
                return {'error': 'Firebase no configurado correctamente'}
            
            # Validar que es una imagen
            if not image_file.content_type.startswith('image/'):
                return {'error': 'El archivo debe ser una imagen'}
            
            # Validar tamaño (máximo 10MB)
            if image_file.size > 10 * 1024 * 1024:
                return {'error': 'La imagen es demasiado grande (máximo 10MB)'}
            
            # Procesar la imagen
            processed_image = self.process_image(image_file)
            if not processed_image:
                return {'error': 'Error procesando la imagen'}
            
            # Generar nombre único
            file_extension = 'jpg'  # Siempre guardar como JPG
            unique_filename = f"foto_{uuid.uuid4().hex}.{file_extension}"
            storage_path = f"{entity_type}/{entity_id}/{unique_filename}"
            
            print(f"📤 Subiendo a Firebase: {storage_path}")
            
            # Subir a Firebase Storage
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            
            # Configurar metadatos
            blob.metadata = {
                'uploaded_by': 'genetics_app',
                'entity_type': entity_type,
                'entity_id': str(entity_id)
            }
            
            # Subir el archivo procesado
            blob.upload_from_string(
                processed_image.getvalue(),
                content_type='image/jpeg'
            )
            
            # IMPORTANTE: Hacer público el archivo
            blob.make_public()
            
            # Obtener URL pública
            public_url = blob.public_url
            
            print(f"✅ Imagen subida exitosamente: {public_url}")
            
            # Verificar que la URL es accesible
            try:
                response = requests.head(public_url, timeout=5)
                if response.status_code != 200:
                    print(f"⚠️ URL no accesible inmediatamente (status: {response.status_code})")
            except:
                print(f"⚠️ No se pudo verificar la URL inmediatamente")
            
            return {
                'success': True,
                'url': public_url,
                'storage_path': storage_path,
                'bucket': self.bucket_name
            }
            
        except Exception as e:
            print(f"❌ Error subiendo imagen: {e}")
            return {'error': f'Error subiendo imagen: {str(e)}'}
    
    def process_image(self, image_file):
        """
        Procesar imagen: redimensionar y optimizar
        """
        try:
            # Abrir imagen con PIL
            image = Image.open(image_file)
            
            # Convertir a RGB si es necesario
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Redimensionar si es muy grande (máximo 800x800)
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                print(f"🔄 Imagen redimensionada a: {image.size}")
            
            # Guardar en memoria con compresión
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            print(f"✅ Imagen procesada: {len(output.getvalue())} bytes")
            return output
            
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return None
    
    def delete_image(self, storage_path):
        """
        Eliminar imagen de Firebase Storage
        """
        try:
            if not self.initialize_firebase():
                return False
            
            bucket = storage.bucket()
            blob = bucket.blob(storage_path)
            
            if blob.exists():
                blob.delete()
                print(f"🗑️ Imagen eliminada: {storage_path}")
                return True
            else:
                print(f"⚠️ Imagen no encontrada: {storage_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error eliminando imagen: {e}")
            return False
    
    def extract_storage_path_from_url(self, url):
        """
        Extraer el storage_path de una URL de Firebase
        """
        try:
            # URL ejemplo: https://storage.googleapis.com/genetics-426ea.appspot.com/animales/4/foto_123.jpg
            if 'storage.googleapis.com' in url and self.bucket_name in url:
                # Buscar la parte después del bucket name
                bucket_part = f"storage.googleapis.com/{self.bucket_name}/"
                if bucket_part in url:
                    storage_path = url.split(bucket_part)[1].split('?')[0]
                    return storage_path
            return None
        except Exception as e:
            print(f"❌ Error extrayendo storage path: {e}")
            return None

# Instancia global del servicio
firebase_storage = FirebaseStorageService()