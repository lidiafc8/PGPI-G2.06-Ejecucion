# perfil/urls.py

from django.urls import path
from . import views

# app_name = 'perfil' # Si usas namespace, descomenta esta línea

urlpatterns = [
    # 1. Perfil del Cliente (Ruta base: /perfil/)
    path('', views.mi_perfil, name='mi_perfil'),
    
    # 2. Perfil del Administrador (Ruta: /perfil/admin)
    path('admin', views.admin_perfil, name='admin_perfil'),
]