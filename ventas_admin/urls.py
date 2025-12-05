from django.urls import path
from . import views

urlpatterns = [
    path('', views.gestion_ventas, name='ventas_admin_index'),
]
