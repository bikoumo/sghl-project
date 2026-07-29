from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from .api import api


def home(request):
    """
    Vue racine — renvoie un JSON indiquant que l'API est en ligne.
    Utilisé par le Health Check de Render.
    """
    return JsonResponse({
        "status": "success",
        "message": "API SGHL Backend en ligne et opérationnelle",
    })


urlpatterns = [
    # Route racine — réponse JSON pour le Health Check Render
    path('', home, name='home'),

    # Admin Django
    path('admin/', admin.site.urls),

    # API Ninja (tous les endpoints via ce point d'entrée)
    path('api/v2/', api.urls),
]
