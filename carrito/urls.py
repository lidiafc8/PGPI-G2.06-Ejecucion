from django.urls import path
from . import views

urlpatterns = [
    path('', views.carrito, name='carrito'),
    path('carrito/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('carrito/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

]