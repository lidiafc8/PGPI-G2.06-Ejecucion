# perfil/urls.py

from django.urls import path
from . import views

# app_name = 'perfil' # Si usas namespace

urlpatterns = [
    # 🌟 CORRECCIÓN: Usa 'views.mi_perfil' para la URL base ('/perfil/') 🌟
    path('', views.mi_perfil, name='mi_perfil'),
]