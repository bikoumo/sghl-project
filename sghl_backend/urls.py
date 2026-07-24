from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from .api import api

urlpatterns = [
    # Redirection racine vers la documentation Swagger de l'API
    path('', lambda request: redirect('/api/v2/docs')),
    
    # Admin Django
    path('admin/', admin.site.urls),
    
    # API Ninja (tous les endpoints via ce point d'entrée)
    path('api/v2/', api.urls),
]
