from django.shortcuts import render, get_object_or_404
from .models import Producto
from django.db.models import Q

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
        categoria_valor  = categoria_valor.replace('_', ' ') 
        
    else:
        productos_a_mostrar = Producto.objects.filter(esta_destacado=True)
        
    
    
    contexto = {
        'productos_destacados': productos_a_mostrar, 
        # En este caso, categoria_valor es la cadena (ej: 'CORTASETOS_Y_MOTOSIERRAS') o None
        'categoria_actual': categoria_valor, 
    }
    
    return render(request, template_name, contexto)

def detalle_producto(request, pk):
    """
    Muestra la información detallada de un producto y extrae productos de la misma categoría.
    """
    # 1. Obtener el producto principal (si no existe, devuelve 404)
    producto = get_object_or_404(Producto, pk=pk)

    # 2. Obtener la categoría del producto actual
    categoria_actual = producto.categoria

    # 3. Consultar productos relacionados
    productos_relacionados = Producto.objects.filter(
        categoria=categoria_actual
    ).exclude(
        pk=pk  # <-- ¡ESTO EXCLUYE EL PRODUCTO ACTUAL!
    )
    
    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
    }
    
    return render(request, 'detalle_producto.html', contexto)

def buscar_productos(request):
    query = request.GET.get('q', '').strip()
    productos_encontrados = []

    if query:
        query_lower = query.lower()

        # Traemos todos los productos (puedes filtrar por visibilidad si lo deseas)
        todos_productos = Producto.objects.all()

        # Filtramos manualmente comparando con display() y con otros campos
        for producto in todos_productos:
            if (
                query_lower in producto.nombre.lower() or
                query_lower in producto.descripcion.lower() or
                query_lower in producto.fabricante.lower() or
                query_lower in producto.departamento.lower() or
                query_lower in producto.get_seccion_display().lower() or
                query_lower in producto.get_categoria_display().lower()
            ):
                productos_encontrados.append(producto)

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'categoria_actual': f'Resultados para "{query}"' if query else 'Búsqueda',
    }

    return render(request, 'catalogo.html', contexto)