from django.http import HttpResponse
from django.template import loader
from .models import Producto 
from django.shortcuts import render 

def index(request):
  
    productos = Producto.objects.all()

    if productos.exists():
        producto = productos.first()
        contexto = {
            'nombre_articulo': producto.nombre,    
        }    
    else:
        contexto = {
            'nombre_articulo': 'No hay productos disponibles',
        }
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))