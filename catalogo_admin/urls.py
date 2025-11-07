from django.urls import path
from . import views

urlpatterns = [
    # Esta ruta base /catalogoAdmin/
    path('productos/', views.lista_productos, name='lista_productos'),
    path('anadir/', views.anadir_producto, name='anadir_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('mostrar/<int:pk>/', views.mostrar_producto, name='mostrar_producto'),
    
]