from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import uuid
from .models import Producto, UsuarioCliente, CestaCompra, ItemCestaCompra, Pedido, EstadoPedido, TipoEnvio
from django.contrib import messages
from django.http import JsonResponse


# Función de ayuda para obtener opciones únicas de filtro
def obtener_opciones_filtro():
    """Retorna las opciones únicas para los filtros (Fabricante y Rangos de Precio)."""
    # Rangos de precio predefinidos (puedes ajustarlos)
    rangos_precio = [
        (0, 50, "Menos de 50€"),
        (50, 100, "50€ - 100€"),
        (100, 500, "100€ - 500€"),
        (500, 99999, "Más de 500€"),
    ]

    # Obtener valores únicos de Fabricante del modelo Producto
    fabricantes = Producto.objects.values_list('fabricante', flat=True).distinct().order_by('fabricante')
    
    #Nota: Ya no se obtiene la lista de categorías/secciones aquí porque es estática en el template.

    return {
        'precios': rangos_precio,
        'fabricantes': list(fabricantes),
        # 'categorias': [], # No es necesario si no se usa
    }

# El parámetro 'categoria' contendrá el valor de la URL (ej: 'CORTASETOS_Y_MOTOSIERRAS')
def catalogo(request, categoria=None):
    """Maneja la visualización del catálogo y la aplicación de filtros."""
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'catalogo.html'
    filtros_activos = False 

    # Recuperar valores seleccionados del formulario GET
    precio_rango_str = request.GET.get('precio', '')
    fabricante_seleccionado = request.GET.get('fabricante', '')
    # 🌟 CAMBIO: Recuperar el valor del filtro de sección. El nombre del campo es 'seccion_filtro'
    seccion_filtro_seleccionada = request.GET.get('seccion_filtro', '') 
    # El valor de la categoría antigua se ignora: categoria_filtro_seleccionada = request.GET.get('categoria_filtro', '') 


    # 1. Filtro por URL (Categoría) - Mantenemos esta lógica si la usas en otras rutas
    # ... (Lógica de filtrado por URL se mantiene como estaba) ...
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

    # --- 2. Filtros Adicionales por GET (Botón de Búsqueda por Filtro) ---
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

    # 🌟 CAMBIO: 2.3. Filtro por Sección (usando el campo 'seccion' del modelo)
    if seccion_filtro_seleccionada:
        q_filtros &= Q(seccion=seccion_filtro_seleccionada)
        filtros_activos = True

    # Aplicar los filtros combinados
    if q_filtros:
        productos_a_mostrar = productos_a_mostrar.filter(q_filtros)

    # --- Cálculo de euros y centavos (y obtención de opciones de filtro) ---
    for producto in productos_a_mostrar:
        producto.euros = int(producto.precio)
        producto.centavos = int((producto.precio - producto.euros) * 100)

    # Obtener las opciones dinámicas (solo precios y fabricantes)
    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'productos_destacados': productos_a_mostrar,
        'categoria_actual': categoria_display,
        'opciones_filtro': opciones_filtro,
        'filtros_activos': filtros_activos,
        
        # Valores seleccionados para mantener el estado en el formulario:
        'precio_seleccionado': precio_rango_str,
        'fabricante_seleccionado': fabricante_seleccionado,
        # 🌟 CAMBIO: Pasar el valor de la sección seleccionada
        'seccion_filtro_seleccionada': seccion_filtro_seleccionada,
        
        'es_catalogo': template_name == 'catalogo.html', 
    }

    return render(request, template_name, contexto)
# Las demás funciones (index, detalle_producto, buscar_productos, agregar_a_cesta) permanecen IGUAL

def index(request, categoria=None):
    productos_a_mostrar = Producto.objects.all()
    categoria_valor = None
    template_name = 'index.html'

    if categoria:
        categoria_valor = categoria.upper()
        productos_a_mostrar = productos_a_mostrar.filter(categoria=categoria_valor)
        template_name = 'catalogo.html'
        categoria_valor = categoria_valor.replace('_', ' ')
    else:
        productos_a_mostrar = Producto.objects.filter(esta_destacado=True)

    # --- NUEVO: calcular euros y centavos ---
    for producto in productos_a_mostrar:
        producto.euros = int(producto.precio)
        producto.centavos = int((producto.precio - producto.euros) * 100)

    opciones_filtro = obtener_opciones_filtro()
    contexto = {
        'productos_destacados': productos_a_mostrar,
        'categoria_actual': categoria_valor,
        'opciones_filtro': opciones_filtro, 
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto en home
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, template_name, contexto)

def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categoria_actual = producto.categoria
    productos_relacionados = Producto.objects.filter(categoria=categoria_actual).exclude(pk=pk)

    # --- NUEVO: calcular euros y centavos del producto principal ---
    producto.euros = int(producto.precio)
    producto.centavos = int((producto.precio - producto.euros) * 100)

    # También podemos calcular para los productos relacionados
    for p in productos_relacionados:
        p.euros = int(p.precio)
        p.centavos = int((p.precio - p.euros) * 100)
    
    opciones_filtro = obtener_opciones_filtro()


    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
        'opciones_filtro': opciones_filtro, 
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto en home
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
                # --- NUEVO: calcular euros y centavos ---
                producto.euros = int(producto.precio)
                producto.centavos = int((producto.precio - producto.euros) * 100)
                productos_encontrados.append(producto)

        opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'categoria_actual': f'Resultados para "{query}"' if query else 'Búsqueda',
        'opciones_filtro': opciones_filtro, 
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto en home
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, 'catalogo.html', contexto)


def agregar_a_cesta(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cantidad = int(request.POST.get('cantidad', 1))

    # Usuario registrado
    if request.user.is_authenticated:
        usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=usuario_cliente)
    # Usuario anónimo
    else:
        session_id = request.session.get("cesta_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["cesta_id"] = session_id
        cesta, _ = CestaCompra.objects.get_or_create(session_id=session_id)

    # Crear o actualizar item
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
        return render(request, 'home/seguimiento_pedido.html', context)

    except Pedido.DoesNotExist:
        messages.error(request, "El enlace de seguimiento es incorrecto o el pedido no existe. Por favor, verifica el enlace en tu email.")
        return redirect('home') 
        
    except Exception as e:
        messages.error(request, f"Error inesperado al acceder al seguimiento. Intente más tarde. ({e})")
        return redirect('home')