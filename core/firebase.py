
import os
import firebase_admin
from firebase_admin import credentials

cred_path = os.path.join(os.path.dirname(__file__), 'genetics-426ea-firebase-adminsdk-fbsvc-4756c53f8c.json')
cred = credentials.Certificate(cred_path)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'geneticsimg'  # 👈 tu bucket personalizado
    })

