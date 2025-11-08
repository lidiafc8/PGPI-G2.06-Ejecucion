from django.urls import path
from . import views

urlpatterns = [
    path('', views.registro, name='registro_usuario_index'),
]