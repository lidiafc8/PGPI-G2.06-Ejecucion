from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

from home.models import Producto




def index(request):
    listaproductos = Producto.objects.filter(esta_destacado=True)   
    contexto = {
        'productos_destacados': listaproductos,
        
    }
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))