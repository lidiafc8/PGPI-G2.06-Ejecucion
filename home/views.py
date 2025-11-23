from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import uuid
from .models import Producto, UsuarioCliente, CestaCompra, ItemCestaCompra
from django.contrib import messages
from django.http import JsonResponse


# Función de ayuda para obtener opciones únicas de filtro
def obtener_opciones_filtro():
    """Retorna las opciones únicas para los filtros (Fabricante y Rangos de Precio)."""
    rangos_precio = [
        (0, 50, "Menos de 50€"),
        (50, 100, "50€ - 100€"),
        (100, 500, "100€ - 500€"),
        (500, 99999, "Más de 500€"),
    ]

    fabricantes = Producto.objects.values_list('fabricante', flat=True).distinct().order_by('fabricante')
    
    return {
        'precios': rangos_precio,
        'fabricantes': list(fabricantes),
    }

# --- ESTA FUNCIÓN 'HOME' LA DEJO POR SI ACASO, PERO LA IMPORTANTE ES 'INDEX' ---
def home(request):
    productos_destacados = Producto.objects.filter(stock__gt=0).order_by('-id')[:5] 
    productos_random = Producto.objects.filter(stock__gt=0).order_by('?')[:10]

    context = {
        'productos_destacados': productos_destacados,
        'productos_random': productos_random,
    }
    return render(request, 'home.html', context)


# --- ESTA ES LA FUNCIÓN QUE USAS: INDEX (MODIFICADA) ---
def index(request, categoria=None):
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'index.html' # Asegúrate de que esto cargue tu plantilla correcta (home.html o index.html)

    if categoria:
        categoria_valor = categoria.upper()
        productos_a_mostrar = productos_a_mostrar.filter(categoria=categoria_valor)
        template_name = 'catalogo.html'
        categoria_valor = categoria_valor.replace('_', ' ')
    else:
        # Aquí carga los productos del carrusel de arriba
        productos_a_mostrar = Producto.objects.filter(esta_destacado=True)

    # 1. Calcular precio (euros/centavos) para el carrusel de ARRIBA
    for producto in productos_a_mostrar:
        producto.euros = int(producto.precio)
        producto.centavos = int((producto.precio - producto.euros) * 100)

    # 2. --- NUEVO: Obtener productos para el carrusel de ABAJO (Random) ---
    productos_random = Producto.objects.filter(stock__gt=0).order_by('?')[:10]

    # 3. --- NUEVO: Calcular precio (euros/centavos) para el carrusel de ABAJO ---
    # (Si no haces esto, saldrá error en el precio de las tarjetas de abajo)
    for p in productos_random:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)

    opciones_filtro = obtener_opciones_filtro()
    
    contexto = {
        'productos_destacados': productos_a_mostrar, # Carrusel Arriba
        'productos_random': productos_random,        # Carrusel Abajo (NUEVO)
        'categoria_actual': categoria_valor,
        'opciones_filtro': opciones_filtro, 
        
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, template_name, contexto)


# --- RESTO DE FUNCIONES (INTACTAS) ---

def catalogo(request, categoria=None):
    """Maneja la visualización del catálogo y la aplicación de filtros."""
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'catalogo.html'
    filtros_activos = False 

    # Recuperar valores seleccionados del formulario GET
    precio_rango_str = request.GET.get('precio', '')
    fabricante_seleccionado = request.GET.get('fabricante', '')
    seccion_filtro_seleccionada = request.GET.get('seccion_filtro', '') 

    # 1. Filtro por URL (Categoría)
    if categoria:
        categoria_valor = categoria.upper()
        productos_a_mostrar = productos_a_mostrar.filter(categoria=categoria_valor)
        categoria_display = categoria_valor.replace('_', ' ')
    else:
        if request.resolver_match.url_name == 'home': 
            productos_a_mostrar = Producto.objects.filter(esta_destacado=True)
            template_name = 'index.html'
            categoria_display = None
        elif request.resolver_match.url_name == 'filtros_globales':
            categoria_display = 'CATÁLOGO CON FILTROS'
        else:
            categoria_display = 'CATÁLOGO COMPLETO'

    # 2. Filtros Adicionales
    q_filtros = Q()
    
    # 2.1. Filtro por Precio
    if precio_rango_str:
        try:
            min_precio, max_precio = map(float, precio_rango_str.split('-'))
            q_filtros &= Q(precio__gte=min_precio) & Q(precio__lte=max_precio)
            filtros_activos = True
        except ValueError:
            pass
    
    # 2.2. Filtro por Fabricante
    if fabricante_seleccionado:
        q_filtros &= Q(fabricante__iexact=fabricante_seleccionado)
        filtros_activos = True

    # 2.3. Filtro por Sección
    if seccion_filtro_seleccionada:
        q_filtros &= Q(seccion=seccion_filtro_seleccionada)
        filtros_activos = True

    # Aplicar filtros
    if q_filtros:
        productos_a_mostrar = productos_a_mostrar.filter(q_filtros)

    # Calcular precio
    for producto in productos_a_mostrar:
        producto.euros = int(producto.precio)
        producto.centavos = int((producto.precio - producto.euros) * 100)

    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'productos_destacados': productos_a_mostrar,
        'categoria_actual': categoria_display,
        'opciones_filtro': opciones_filtro,
        'filtros_activos': filtros_activos,
        'precio_seleccionado': precio_rango_str,
        'fabricante_seleccionado': fabricante_seleccionado,
        'seccion_filtro_seleccionada': seccion_filtro_seleccionada,
        'es_catalogo': template_name == 'catalogo.html', 
    }

    return render(request, template_name, contexto)

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categoria_actual = producto.categoria
    productos_relacionados = Producto.objects.filter(categoria=categoria_actual).exclude(pk=pk)

    producto.euros = int(producto.precio)
    producto.centavos = int((producto.precio - producto.euros) * 100)

    for p in productos_relacionados:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)
    
    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'opciones_filtro': opciones_filtro, 
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, 'detalle_producto.html', contexto)

def buscar_productos(request):
    query = request.GET.get('q', '').strip()
    productos_encontrados = []

    if query:
        query_lower = query.lower()
        todos_productos = Producto.objects.all()

        for producto in todos_productos:
            if (
                query_lower in producto.nombre.lower() or
                query_lower in producto.descripcion.lower() or
                query_lower in producto.fabricante.lower() or
                query_lower in producto.departamento.lower() or
                query_lower in producto.get_seccion_display().lower() or
                query_lower in producto.get_categoria_display().lower()
            ):
                producto.euros = int(producto.precio)
                producto.centavos = int((producto.precio - producto.euros) * 100)
                productos_encontrados.append(producto)

    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'categoria_actual': f'Resultados para "{query}"' if query else 'Búsqueda',
        'opciones_filtro': opciones_filtro, 
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, 'catalogo.html', contexto)


def agregar_a_cesta(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if request.user.is_authenticated:
        usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=usuario_cliente)
    else:
        session_id = request.session.get("cesta_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["cesta_id"] = session_id
        cesta, _ = CestaCompra.objects.get_or_create(session_id=session_id)

    item, creado = ItemCestaCompra.objects.get_or_create(
        cesta_compra=cesta,
        producto=producto,
        defaults={"cantidad": cantidad, "precio_unitario": producto.precio}
    )
    if not creado:
        item.cantidad += cantidad
    item.precio_unitario = producto.precio
    item.save()

    total_items = sum(i.cantidad for i in cesta.items.all())

    return JsonResponse({
        "success": True,
        "mensaje": f"✅ {producto.nombre} añadido correctamente a la cesta.",
        "total_items": total_items
    })