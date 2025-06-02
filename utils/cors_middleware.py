"""
Middleware CORS personalizado que siempre agrega cabeceras CORS
"""
from django.http import JsonResponse
import traceback

class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Manejar OPTIONS requests inmediatamente
        if request.method == 'OPTIONS':
            response = JsonResponse({'status': 'ok'})
            return self.add_cors_headers(request, response)
        
        try:
            response = self.get_response(request)
        except Exception as e:
            # Si hay una excepción, crear una respuesta de error con CORS
            print(f"❌ Error en middleware: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            
            response = JsonResponse({
                'error': 'Internal Server Error',
                'message': str(e),
                'type': type(e).__name__
            }, status=500)
        
        return self.add_cors_headers(request, response)

    def add_cors_headers(self, request, response):
        """Agregar cabeceras CORS a cualquier respuesta"""
        
        # Obtener el origen de la solicitud
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # En desarrollo, permitir cualquier origen local
        allowed_origins = [
            'http://localhost:5173',
            'http://127.0.0.1:5173',
            'http://localhost:3000',
            'http://127.0.0.1:3000',
        ]
        
        # Siempre agregar cabeceras CORS en desarrollo
        if origin in allowed_origins or not origin:
            response['Access-Control-Allow-Origin'] = origin or 'http://localhost:5173'
        else:
            response['Access-Control-Allow-Origin'] = '*'
            
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        
        # Debug
        print(f"🔧 CORS headers added to {request.method} {request.path}")
        print(f"   Origin: {origin}")
        print(f"   Allow-Origin: {response.get('Access-Control-Allow-Origin')}")
        
        return response