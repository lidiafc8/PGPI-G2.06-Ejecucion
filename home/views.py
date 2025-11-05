from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from .models import Escaparate, Articulo

def index(request):
    escaparates = Escaparate.objects.all()
    escaparate = escaparates.first()
    articulos = Articulo.objects.filter(pk = escaparate.articulo.id)
    articulo = articulos.first()
    contexto = {
        'nombre_articulo': articulo.nombre,
    }
    plantilla = loader.get_template('index.html')
    return HttpResponse(plantilla.render(contexto, request))