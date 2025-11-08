from django.shortcuts import render, get_object_or_404
from .models import Producto, Categoria # Importamos Categoria (la enumeración)

# El parámetro 'categoria' contendrá el valor de la URL (ej: 'CORTASETOS_Y_MOTOSIERRAS')
def index(request, categoria=None):
    
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None # Usaremos esta variable para guardar el valor de la categoría
    template_name = 'index.html' 

    # 1. Lógica Condicional: Determinar el filtro y la plantilla
    if categoria:
        # CASO 1: URL contiene un SLUG (Ej: /subcategorias/CORTASETOS_Y_MOTOSIERRAS/)
        
        # El valor de la URL ya es la cadena que necesitas. 
        # NOTA: Las URL con slug suelen ser minúsculas con guiones.
        # Si tu slug en la URL viene en mayúsculas (como CORTASETOS_Y_MOTOSIERRAS), 
        # úsalo directamente. Si Django lo convierte a minúsculas, úsalo en minúsculas.
        
        categoria_valor = categoria.upper() # Asumo que lo tienes en mayúsculas en el modelo
        
        
        # Filtramos los productos directamente en el campo CharField.
        # 'categoria' es un campo de Producto.
        productos_a_mostrar = productos_a_mostrar.filter(categoria=categoria_valor)
        
        template_name = 'catalogo.html' 
        categoria_valor = categoria_formateada = categoria_valor.replace('_', ' ') 
        
    else:
        productos_a_mostrar = Producto.objects.filter(esta_destacado=True)
        
    
    
    contexto = {
        'productos_destacados': productos_a_mostrar, 
        # En este caso, categoria_valor es la cadena (ej: 'CORTASETOS_Y_MOTOSIERRAS') o None
        'categoria_actual': categoria_valor, 
    }
    
    return render(request, template_name, contexto)