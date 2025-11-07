from django.http import HttpResponse
from django.template import loader
<<<<<<< HEAD
from django.shortcuts import render

from home.models import Producto




def index(request):
    listaproductos = Producto.objects.filter(esta_destacado=True)   
    contexto = {
        'productos_destacados': listaproductos,
        
    }
=======
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
>>>>>>> 886e90c34da5004bc1824abd315461e58d8b2d44
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))