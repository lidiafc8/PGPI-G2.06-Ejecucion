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
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='home'),
    path('subcategorias/<slug:categoria>/', views.index, name='productos_por_categoria'),    
    path('catalogoAdmin/', include('catalogo_admin.urls')),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('adminpanel/', include('adminpanel.urls')),
    path('ventas_admin/', include('ventas_admin.urls')),
    path('clientes_admin/', include('clientes_admin.urls')),
    path('registro/', include('registro_usuario.urls')),
    path('inicio_sesion/', include('inicio_sesion.urls')),
    
]

# BLOQUE CONDICIONAL AÑADIDO:
# Esto solo se ejecuta cuando DEBUG=True, permitiendo que el servidor local sirva estáticos.
if settings.DEBUG:
    # Mapea /static/ a la carpeta definida en STATICFILES_DIRS.
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




