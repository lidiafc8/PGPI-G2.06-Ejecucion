from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

from home.models import Producto



def index(request):
    escaparates = Producto.objects.all()
    escaparate = escaparates.first()
    contexto = {
        'nombre_articulo': escaparate,
    }
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))