from django.urls import path
from . import views
app_name = 'carrito'
urlpatterns = [
    path('', views.ver_cesta, name='carrito'),
    path('update/<int:producto_id>/', views.update_cart, name='update_cart'),
    path('remove/<int:producto_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('pago/', views.checkout, name='checkout'),
    path('procesar/', views.procesar_pago, name='procesar_pago')

]