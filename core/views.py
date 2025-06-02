from django.http import JsonResponse
from django.db import connection
from datetime import datetime

def health_check(request):
    """Health check básico"""
    try:
        # Test básico de la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "database": "connected"
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }, status=500)