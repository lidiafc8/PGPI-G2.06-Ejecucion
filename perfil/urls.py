from django.urls import path
from . import views


urlpatterns = [
    path('', views.mi_perfil, name='mi_perfil'),
    path('admin', views.admin_perfil, name='admin_perfil'),
    path('pedidos/', views.lista_pedidos_cliente, name='lista_pedidos_cliente'),
    path('pedidos/<int:pedido_id>/ticket/', views.ver_ticket_pedido, name='ver_ticket'),
]