from django.urls import path
from . import views

urlpatterns = [
    # Esta ruta base /catalogoAdmin/
    path('', views.lista_productos, name='lista_productos'),
    path('anadir/', views.anadir_producto, name='anadir_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    
]