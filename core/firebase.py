# core/firebase.py - Configuración simplificada

import os
import firebase_admin
from firebase_admin import credentials, storage

def initialize_firebase():
    """Inicializar Firebase con manejo de errores mejorado"""
    try:
        # Verificar si ya está inicializado
        if firebase_admin._apps:
            print("✅ Firebase ya inicializado")
            return firebase_admin.get_app()
        
        # Buscar archivo de credenciales
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Ir al directorio raíz del proyecto
        possible_paths = [
            os.path.join(base_dir, 'core', 'genetics-426ea-firebase-adminsdk-fbsvc-479eb4f610.json'),
            os.path.join(base_dir, 'genetics-426ea-firebase-adminsdk-fbsvc-479eb4f610.json'),
            os.path.join(os.path.dirname(__file__), 'genetics-426ea-firebase-adminsdk-fbsvc-479eb4f610.json'),
        ]
        
        cred_path = None
        for path in possible_paths:
            if os.path.exists(path):
                cred_path = path
                print(f"✅ Credenciales encontradas: {path}")
                break
        
        if not cred_path:
            print("❌ Archivo de credenciales no encontrado en:")
            for path in possible_paths:
                print(f"   - {path}")
            raise FileNotFoundError("Archivo de credenciales Firebase no encontrado")
        
        # Inicializar Firebase
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred, {
            'storageBucket': 'geneticsimg'  # Tu bucket
        })
        
        print("✅ Firebase inicializado correctamente")
        return app
        
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")
        raise e

def get_storage_bucket():
    """Obtener bucket de storage"""
    try:
        # Inicializar si no está inicializado
        if not firebase_admin._apps:
            initialize_firebase()
        
        bucket = storage.bucket()
        print(f"✅ Bucket obtenido: {bucket.name}")
        return bucket
        
    except Exception as e:
        print(f"❌ Error obteniendo bucket: {e}")
        raise e

def test_connection():
    """Test de conexión"""
    try:
        bucket = get_storage_bucket()
        # Intentar listar archivos
        blobs = list(bucket.list_blobs(max_results=1))
        print(f"✅ Test de conexión exitoso - Bucket: {bucket.name}")
        return True
    except Exception as e:
        print(f"❌ Test de conexión fallido: {e}")
        return False

# Inicializar automáticamente solo si no hay errores
try:
    initialize_firebase()
except:
    print("⚠️ Firebase no se pudo inicializar automáticamente")