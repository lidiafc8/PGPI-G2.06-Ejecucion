from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import uuid
from .models import Producto, UsuarioCliente, CestaCompra, ItemCestaCompra, Pedido, EstadoPedido, TipoEnvio
from django.contrib import messages
from django.http import JsonResponse

# --- HELPER PARA FILTROS ---
def obtener_opciones_filtro():
    """Retorna las opciones únicas para los filtros."""
    rangos_precio = [
        (0, 50, "Menos de 50€"),
        (50, 100, "50€ - 100€"),
        (100, 500, "100€ - 500€"),
        (500, 99999, "Más de 500€"),
    ]
    fabricantes = Producto.objects.values_list('fabricante', flat=True).distinct().order_by('fabricante')
    return { 'precios': rangos_precio, 'fabricantes': list(fabricantes) }

# -------------------------------------------------------------------------
# VISTA PRINCIPAL (ESTA ES LA QUE MANDA AHORA)
# -------------------------------------------------------------------------
def index(request, categoria=None):
    template_name = 'index.html' # Asumo que tu template de portada se llama home.html o index.html
    categoria_valor = None
    
    # 1. LOGICA DE SELECCIÓN DE PRODUCTOS (CARRUSEL ARRIBA)
    if categoria:
        # Si hay categoría en la URL, filtramos por esa categoría
        categoria_valor = categoria.upper()
        productos_principal = Producto.objects.filter(categoria=categoria_valor)
        template_name = 'catalogo.html' # Cambiamos template si es categoría
        categoria_valor = categoria_valor.replace('_', ' ')
    else:
        # SI ESTAMOS EN LA PORTADA:
        # AQUÍ ESTÁ EL FILTRO IMPORTANTE. Solo carga los que tienen el check puesto.
        productos_principal = Producto.objects.filter(esta_destacado=True)
    #Nota: Ya no se obtiene la lista de categorías/secciones aquí porque es estática en el template.

    # 2. PRODUCTOS DE ABAJO (Grid de 6 destacados)
    # Filtramos que tengan stock, que sean destacados y cogemos 6 aleatorios
    productos_abajo = Producto.objects.filter(stock__gt=0, esta_destacado=True).order_by('?')[:6]

    # 3. CALCULOS DE PRECIO (EUROS/CENTAVOS)
    for p in productos_principal:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)

    for p in productos_abajo:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)

    contexto = {
        'productos_destacados': productos_principal, # Carrusel Arriba
        'productos_random': productos_abajo,         # Carrusel Abajo
        'categoria_actual': categoria_valor,
        'opciones_filtro': obtener_opciones_filtro(),
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
        'plantilla_base': 'base.html',
    }
    
    # Si por alguna razón tu archivo se llama home.html en vez de index.html, cambia esto abajo:
    return render(request, template_name, contexto)


# -------------------------------------------------------------------------
# RESTO DE VISTAS (CATÁLOGO, DETALLE, ETC)
# -------------------------------------------------------------------------

def catalogo(request, categoria=None):
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'catalogo.html'
    filtros_activos = False 

    # Recuperar filtros del GET
    precio_rango_str = request.GET.get('precio', '')
    fabricante_seleccionado = request.GET.get('fabricante', '')
    seccion_filtro_seleccionada = request.GET.get('seccion_filtro', '') 

    if categoria:
        categoria_valor = categoria.upper()
        productos_a_mostrar = productos_a_mostrar.filter(categoria=categoria_valor)
        categoria_display = categoria_valor.replace('_', ' ')
    else:
        # Lógica de fallback
        if request.resolver_match.url_name == 'home': 
            # Si se llama desde home, filtrar destacados
            productos_a_mostrar = Producto.objects.filter(esta_destacado=True)
            template_name = 'index.html'
            categoria_display = None
        elif request.resolver_match.url_name == 'filtros_globales':
            categoria_display = 'CATÁLOGO CON FILTROS'
        else:
            categoria_display = 'CATÁLOGO COMPLETO'

    # Aplicar filtros
    q_filtros = Q()
    if precio_rango_str:
        try:
            min_precio, max_precio = map(float, precio_rango_str.split('-'))
            q_filtros &= Q(precio__gte=min_precio) & Q(precio__lte=max_precio)
            filtros_activos = True
        except ValueError: pass
    
    if fabricante_seleccionado:
        q_filtros &= Q(fabricante__iexact=fabricante_seleccionado)
        filtros_activos = True

    if seccion_filtro_seleccionada:
        q_filtros &= Q(seccion=seccion_filtro_seleccionada)
        filtros_activos = True

    if q_filtros:
        productos_a_mostrar = productos_a_mostrar.filter(q_filtros)

    for p in productos_a_mostrar:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)

    contexto = {
        'productos_destacados': productos_a_mostrar,
        'categoria_actual': categoria_display,
        'opciones_filtro': obtener_opciones_filtro(),
        'filtros_activos': filtros_activos,
        'precio_seleccionado': precio_rango_str,
        'fabricante_seleccionado': fabricante_seleccionado,
        'seccion_filtro_seleccionada': seccion_filtro_seleccionada,
        'es_catalogo': template_name == 'catalogo.html', 
    }
    return render(request, template_name, contexto)

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    # Precios
    producto.euros = int(producto.precio)
    producto.centavos = int((producto.precio - producto.euros) * 100)

    productos_relacionados = Producto.objects.filter(categoria=producto.categoria).exclude(pk=pk)
    for p in productos_relacionados:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)

    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'opciones_filtro': obtener_opciones_filtro(), 
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
        todos = Producto.objects.all()
        for p in todos:
            if (query_lower in p.nombre.lower() or 
                query_lower in p.fabricante.lower() or 
                query_lower in p.get_categoria_display().lower()):
                p.euros = int(p.precio)
                p.centavos = int((p.precio - p.euros) * 100)
                productos_encontrados.append(p)

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'categoria_actual': f'Resultados: {query}',
        'opciones_filtro': obtener_opciones_filtro(), 
        'precio_seleccionado': '', 'fabricante_seleccionado': '', 'seccion_filtro_seleccionada': '',
    }
    return render(request, 'catalogo.html', contexto)

def agregar_a_cesta(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if request.user.is_authenticated:
        # Lógica usuario registrado
        try:
            cliente = UsuarioCliente.objects.get(usuario=request.user)
        except UsuarioCliente.DoesNotExist:
            # Crear cliente si no existe (parche rápido)
            cliente = UsuarioCliente.objects.create(usuario=request.user)
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=cliente)
    else:
        # Lógica usuario anónimo
        session_id = request.session.get("cesta_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["cesta_id"] = session_id
        cesta, _ = CestaCompra.objects.get_or_create(session_id=session_id)

    item, creado = ItemCestaCompra.objects.get_or_create(
        cesta_compra=cesta, producto=producto,
        defaults={"cantidad": cantidad, "precio_unitario": producto.precio}
    )
    if not creado:
        item.cantidad += cantidad
    item.precio_unitario = producto.precio
    item.save()

    total_items = sum(i.cantidad for i in cesta.items.all())
    return JsonResponse({
        "success": True, 
        "mensaje": f"✅ {producto.nombre} añadido.", 
        "total_items": total_items
        
    })

def _obtener_historial_del_pedido(pedido):
    """
    Define el estado del seguimiento basado en el campo 'estado' del pedido.
    """
    estados_mapeados = [
        {'nombre': 'Pedido Recibido', 'completado': True, 'fecha': pedido.fecha_creacion.strftime('%d/%m/%Y %H:%M')},
        {'nombre': 'En Preparación', 'completado': pedido.estado in [EstadoPedido.ENVIADO, EstadoPedido.ENTREGADO]},
        {'nombre': 'Enviado', 'completado': pedido.estado == EstadoPedido.ENVIADO or pedido.estado == EstadoPedido.ENTREGADO},
        {'nombre': 'Entregado', 'completado': pedido.estado == EstadoPedido.ENTREGADO},
    ]
    for paso in estados_mapeados:
        if paso['completado'] and paso['nombre'] != 'Pedido Recibido':
            paso['fecha'] = "Completado" 

    return estados_mapeados

def seguimiento_pedido(request, order_id, tracking_hash):
    """
    Muestra el estado actual del pedido usando ID y el tracking_id como hash de seguridad.
    """
    try:
        pedido = Pedido.objects.get( 
            id=order_id, 
            tracking_id=tracking_hash
        )
        total = pedido.total_importe
        total_euros = int(total)
        total_centavos = int((total - total_euros) * 100)
        
        context = {
            'pedido': pedido,
            'total_euros': total_euros,
            'total_centavos': total_centavos,
            'estado_actual_display': pedido.get_estado_display(), 
            'historial_estados': _obtener_historial_del_pedido(pedido),
            'opciones_filtro': obtener_opciones_filtro(),
            'precio_seleccionado': '',
            'fabricante_seleccionado': '',
            'seccion_filtro_seleccionada': '',
        }
        return render(request, 'seguimiento_pedido.html', context)

    except Pedido.DoesNotExist:
        # Intentar obtener el pedido solo por ID para informar si hay mismatch de tracking_id
        try:
            pedido_por_id = Pedido.objects.get(id=order_id)
            mensaje = (
                f"Pedido encontrado (ID={order_id}) pero el código de seguimiento no coincide. "
                f"Tracking en DB: {pedido_por_id.tracking_id} | Tracking recibido: {tracking_hash}"
            )
        except Pedido.DoesNotExist:
            mensaje = "El pedido no existe con el ID proporcionado. Por favor, verifica el enlace en tu email."

        messages.error(request, mensaje)
        # Renderizar plantilla de error para mostrar información útil al usuario/desarrollador
        context_error = {
            'message': mensaje,
            'opciones_filtro': obtener_opciones_filtro(),
            'precio_seleccionado': '',
            'fabricante_seleccionado': '',
            'seccion_filtro_seleccionada': '',
        }
        return render(request, 'error_seguimiento.html', context_error)
    except Exception as e:
        # Registrar para depuración y mostrar mensaje de error genérico
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error inesperado en seguimiento_pedido: %s", e)
        messages.error(request, f"Error inesperado al acceder al seguimiento. Intente más tarde. ({e})")
        context_error = {
            'message': f"Error inesperado al acceder al seguimiento. ({e})",
            'opciones_filtro': obtener_opciones_filtro(),
            'precio_seleccionado': '',
            'fabricante_seleccionado': '',
            'seccion_filtro_seleccionada': '',
        }
        return render(request, 'error_seguimiento.html', context_error)