from django.http import HttpResponse
from django.template import loader
<<<<<<< HEAD
from django.shortcuts import render

from home.models import Producto



def index(request):
    escaparates = Producto.objects.all()
    escaparate = escaparates.first()
    contexto = {
        'nombre_articulo': escaparate,
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
>>>>>>> 8bcebad7101cbb28c19397ccf1fc993572a1bbf5
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))