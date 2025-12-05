from django.urls import path
from . import views

urlpatterns = [
    path('lista/', views.lista_pedidos, name='lista_pedidos'),
    path('detalle/<int:pk>/', views.detalle_pedido, name='detalle_pedido'),
]
