import os
import firebase_admin
from firebase_admin import credentials, storage

def initialize_firebase():
    """
    Inicializar Firebase Admin SDK con múltiples ubicaciones posibles
    """
    try:
        # Verificar si ya está inicializado
        if firebase_admin._apps:
            print("Firebase ya está inicializado")
            return firebase_admin.get_app()
        
        # Posibles ubicaciones del archivo de credenciales
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'genetics-426ea-firebase-adminsdk-fbsvc-479eb4f610.json'),
        ]
        
        cred_path = None
        for path in possible_paths:
            if path and os.path.exists(path):
                cred_path = path
                print(f"✅ Archivo de credenciales encontrado en: {path}")
                break
        
        if not cred_path:
            available_paths = "\n".join([f"  - {path}" for path in possible_paths if path])
            raise FileNotFoundError(
                f"Archivo de credenciales de Firebase no encontrado.\n"
                f"Ubicaciones verificadas:\n{available_paths}\n\n"
                f"Por favor:\n"
                f"1. Descarga las credenciales desde Firebase Console\n"
                f"2. Colócalas en una de las ubicaciones anteriores\n"
                f"3. O configura la variable de entorno FIREBASE_CREDENTIALS_PATH"
            )
        
        # Inicializar credenciales
        cred = credentials.Certificate(cred_path)
        
        # Inicializar app con bucket personalizado
        app = firebase_admin.initialize_app(cred, {
            'storageBucket': 'geneticsimg'  # Tu bucket personalizado
        })
        
        print("✅ Firebase inicializado correctamente")
        print(f"📁 Usando credenciales de: {cred_path}")
        return app
        
    except Exception as e:
        print(f"❌ Error inicializando Firebase: {e}")
        return None

def get_storage_bucket():
    """
    Obtener referencia al bucket de storage
    """
    try:
        # Asegurar que Firebase está inicializado
        if not firebase_admin._apps:
            app = initialize_firebase()
            if not app:
                raise Exception("No se pudo inicializar Firebase")
        
        # Obtener bucket
        bucket = storage.bucket()
        return bucket
        
    except Exception as e:
        print(f"Error obteniendo bucket de storage: {e}")
        raise e

def test_firebase_connection():
    """
    Probar conexión a Firebase Storage
    """
    try:
        bucket = get_storage_bucket()
        
        # Intentar listar archivos para probar conectividad
        blobs = list(bucket.list_blobs(max_results=1))
        
        print("✅ Conexión a Firebase Storage exitosa")
        print(f"📦 Bucket: {bucket.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error en conexión a Firebase Storage: {e}")
        return False

# NO inicializar automáticamente para evitar errores
# Firebase se inicializará solo cuando se necesite