from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import uuid
import random
from .models import Producto, UsuarioCliente, CestaCompra, ItemCestaCompra, Pedido, EstadoPedido, TipoEnvio
from django.contrib import messages
from django.http import JsonResponse

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

def _calcular_desglose_precio(queryset):
    """
    Añade los atributos .euros y .centavos a cada producto de una lista o queryset.
    """

    if not isinstance(queryset, list):
        queryset = list(queryset)

    for p in queryset:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)
    return queryset

def index(request, categoria=None):
    template_name = 'index.html'
    categoria_valor = None

    if categoria:

        categoria_valor = categoria.upper()
        productos_principal = Producto.objects.filter(categoria=categoria_valor)
        template_name = 'catalogo.html'
        categoria_valor = categoria_valor.replace('_', ' ')
    else:

        productos_principal = Producto.objects.filter(esta_destacado=True)

    productos_abajo = Producto.objects.filter(stock__gt=0).order_by('?')[:10]

    _calcular_desglose_precio(productos_principal)
    _calcular_desglose_precio(productos_abajo)

    contexto = {
        'productos_destacados': productos_principal,
        'productos_random': productos_abajo,
        'categoria_actual': categoria_valor,
        'opciones_filtro': obtener_opciones_filtro(),
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
        'plantilla_base': 'base.html',
    }

    return render(request, template_name, contexto)

def catalogo(request, categoria=None):
    """
    Vista específica para listados con filtros laterales.
    """
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'catalogo.html'
    filtros_activos = False

    precio_rango_str = request.GET.get('precio', '')
    fabricante_seleccionado = request.GET.get('fabricante', '')
    seccion_filtro_seleccionada = request.GET.get('seccion_filtro', '')

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

    productos_random = Producto.objects.filter(stock__gt=0).order_by('?')[:10]

    _calcular_desglose_precio(productos_a_mostrar)
    _calcular_desglose_precio(productos_random)

    contexto = {
        'productos_destacados': productos_a_mostrar,
        'productos_random': productos_random,
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

    producto.euros = int(producto.precio)
    producto.centavos = int((producto.precio - producto.euros) * 100)

    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria
    ).exclude(
        pk=pk
    ).order_by('?')[:10]

    _calcular_desglose_precio(productos_relacionados)

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

        todos = Producto.objects.all()
        query_lower = query.lower()
        for p in todos:
            if (query_lower in p.nombre.lower() or
                query_lower in p.fabricante.lower() or
                query_lower in p.get_categoria_display().lower()):
                p.euros = int(p.precio)
                p.centavos = int((p.precio - p.euros) * 100)
                productos_encontrados.append(p)

    productos_random = Producto.objects.filter(stock__gt=0).order_by('?')[:10]
    _calcular_desglose_precio(productos_random)

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'productos_random': productos_random,
        'categoria_actual': f'Resultados: {query}',
        'opciones_filtro': obtener_opciones_filtro(),
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, 'catalogo.html', contexto)

def agregar_a_cesta(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    if cantidad > producto.stock:
        return JsonResponse({
             "success": False,
             "mensaje": f"❌ Solo quedan {producto.stock} unidades."
         })

    if request.user.is_authenticated:

        cliente, _ = UsuarioCliente.objects.get_or_create(usuario=request.user)
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=cliente)
    else:
        session_id = request.session.get("cesta_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["cesta_id"] = session_id
        cesta, _ = CestaCompra.objects.get_or_create(session_id=session_id)

    item, creado = ItemCestaCompra.objects.get_or_create(
        cesta_compra=cesta, producto=producto,
        defaults={"cantidad": cantidad, "precio_unitario": producto.precio}
    )

    cantidad_final = item.cantidad + cantidad if not creado else cantidad

    if cantidad_final > producto.stock:
        return JsonResponse({
            "success": False,
            "mensaje": f"❌ Stock insuficiente. Máximo: {producto.stock}"
        })

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
    try:
        pedido = Pedido.objects.get(id=order_id, tracking_id=tracking_hash)

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

        try:

            pedido_por_id = Pedido.objects.get(id=order_id)
            mensaje = f"Error de seguridad: El código de seguimiento no coincide para el pedido {order_id}."
        except Pedido.DoesNotExist:
            mensaje = "El pedido no existe."

        messages.error(request, mensaje)

        context_error = {
            'message': mensaje,
            'opciones_filtro': obtener_opciones_filtro(),
            'precio_seleccionado': '', 'fabricante_seleccionado': '', 'seccion_filtro_seleccionada': '',
        }
        return render(request, 'error_seguimiento.html', context_error)

    except Exception as e:
        messages.error(request, f"Error inesperado: {e}")
        return render(request, 'error_seguimiento.html', {
            'message': "Error del servidor.",
            'opciones_filtro': obtener_opciones_filtro(),
            'precio_seleccionado': '', 'fabricante_seleccionado': '', 'seccion_filtro_seleccionada': '',
        })
