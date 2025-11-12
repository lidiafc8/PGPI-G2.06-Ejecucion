from django.urls import path
from . import views


urlpatterns = [
    path('', views.mi_perfil, name='mi_perfil'),
    
    path('admin', views.admin_perfil, name='admin_perfil'),
]