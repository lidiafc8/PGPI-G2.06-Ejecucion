"""
URL configuration for mundo_jardin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home import views 
from carrito import views as carrito_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls),
    path('filtros/', views.catalogo, name='filtros_globales'),
    path('subcategorias/<slug:categoria>/', views.index, name='productos_por_categoria'),    
    path('catalogoAdmin/', include('catalogo_admin.urls')),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('buscar/', views.buscar_productos, name='buscar'),
    path('adminpanel/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),
    path('ventas_admin/', include('ventas_admin.urls')),
    path('clientes_admin/', include('clientes_admin.urls')),
    path('registro/', include(('registro_usuario.urls', 'registro_usuario'), namespace='registro')),
    path('inicio_sesion/', include('inicio_sesion.urls')),
    path('perfil/', include(('perfil.urls','perfil'), namespace='perfil')),
    path('info_tienda/', include(('info_tienda.urls','info_tienda'), namespace='info_tienda')),
    path('carrito/', include(('carrito.urls','carrito'), namespace='carrito')),
    path('cesta/agregar/<int:producto_id>/', views.agregar_a_cesta, name='agregar_a_cesta'),
    path('cesta/', carrito_views.ver_cesta, name='ver_cesta'),
    path('pedidos/', include('pedidos_admin.urls')),
    path('seguimiento/<int:order_id>/<str:tracking_hash>/', views.seguimiento_pedido, name='seguimiento_pedido')
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
