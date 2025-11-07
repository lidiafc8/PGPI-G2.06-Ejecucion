from django.urls import path
from . import views

urlpatterns = [
    path('', views.gestion_clientes, name='clientes_admin_index'),
    path('eliminar/<int:cliente_id>/', views.cliente_eliminar_confirmar, name='cliente_eliminar_confirmar'),
]