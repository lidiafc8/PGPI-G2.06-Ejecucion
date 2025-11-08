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
    
    # Opcional: Para que el carrusel sea más dinámico, puedes añadir:
    # .order_by('?') 
    # Y limitar si tienes miles de productos:
    # .order_by('?')[:20] 

    # 4. Preparar el contexto
    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
    }
    
    return render(request, 'detalle_producto.html', contexto)

def buscar_productos(request):
    # 1. Obtener el término de búsqueda
    query = request.GET.get('q')
    productos_encontrados = []
    
    # 2. Lógica de filtrado
    if query:
        # Filtra productos donde el 'nombre' contiene la consulta (icontains)
        # Puedes añadir más campos a la búsqueda, por ejemplo:
        productos_encontrados = Producto.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(fabricante__icontains=query)|
            Q(departamento__icontains=query)
        ).distinct() # Usa distinct() para evitar duplicados si hay múltiples coincidencias

    # 3. Prepara el contexto y renderiza
    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados, # Usamos el mismo nombre que en index.html si quieres reutilizar la plantilla
        'categoria_actual': f'Resultados para "{query}"' if query else 'Búsqueda',
    }
    
    # Podrías reutilizar la plantilla 'catalogo.html' o 'index.html' si muestra listas de productos
    return render(request, 'catalogo.html', contexto)