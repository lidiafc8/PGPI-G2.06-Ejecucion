from django.urls import path
from . import views

urlpatterns = [

    path('productos/', views.lista_productos, name='lista_productos'),
    path('anadir/', views.anadir_producto, name='anadir_producto'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('mostrar/<int:pk>/', views.mostrar_producto, name='mostrar_producto'),
    path('productos/guardar-orden/', views.guardar_orden_productos, name='guardar_orden_productos'),
    path('cargar-categorias/', views.cargar_categorias, name='cargar_categorias'),

]
