from django.contrib import admin
from django.urls import path, include
from .api import api

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),
    
    # API Ninja (tous les endpoints via ce point d'entrée)
    path('api/v2/', api.urls),
]