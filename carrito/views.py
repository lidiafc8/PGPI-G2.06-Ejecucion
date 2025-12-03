from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from decimal import Decimal
from django.contrib import messages
from django.db import transaction
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.db.models import Q
import uuid

# Importación de tus modelos
from home.models import (
    Producto, CestaCompra, UsuarioCliente, ItemCestaCompra,
    Pedido, ItemPedido, TipoPago, TipoEnvio, EstadoPedido, Tarjeta
)

# --- FUNCIÓN AUXILIAR PARA FILTROS (Recuperada) ---
def obtener_opciones_filtro():
    fabricantes = Producto.objects.values_list('fabricante', flat=True).distinct().order_by('fabricante')
    precios = [
        (0, 50, 'Menos de 50€'),
        (50, 100, '50€ - 100€'),
        (100, 500, '100€ - 500€'),
        (500, 99999, 'Más de 500€'),
    ]
    return {
        'fabricantes': list(fabricantes),
        'precios': precios,
    }

# ==============================================================================
# 1. VISTAS DE LA TIENDA (INICIO, DETALLE, CATEGORÍAS)
# ==============================================================================

def index(request):
    """Vista de la Página de Inicio"""
    # Carrusel superior
    productos_destacados = Producto.objects.filter(stock__gt=0).order_by('?')[:5]
    # Grid inferior
    productos_random = Producto.objects.filter(stock__gt=0).order_by('?')[:6]
    
    opciones_filtro = obtener_opciones_filtro()
    
    contexto = {
        'productos_destacados': productos_destacados,
        'productos_random': productos_random,
        'opciones_filtro': opciones_filtro,
        'categoria_actual': 'Inicio',
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
        'plantilla_base': 'base.html'
    }
    # IMPORTANTE: Asegúrate de que tu template se llame 'index.html' o 'home.html'
    return render(request, 'index.html', contexto) 

def detalle_producto(request, pk):
    """Vista de Ficha de Producto"""
    producto = get_object_or_404(Producto, pk=pk)
    
    # Productos relacionados (misma categoría, excluyendo el actual)
    productos_relacionados = Producto.objects.filter(
        categoria=producto.categoria, 
        stock__gt=0
    ).exclude(pk=pk).order_by('?')[:5]
    
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

def productos_por_categoria(request, categoria):
    """Vista de Listado por Categoría"""
    productos = Producto.objects.filter(categoria=categoria)
    
    # Si no hay productos, intentamos buscar por sección si el modelo lo permite
    if not productos.exists():
        productos = Producto.objects.filter(seccion=categoria)

    opciones_filtro = obtener_opciones_filtro()
    
    # Nombre legible para el título
    categoria_display = categoria.replace('_', ' ').upper()

    contexto = {
        'categoria_actual': categoria_display,
        'productos_destacados': productos, # Usamos la misma variable que en el template
        'opciones_filtro': opciones_filtro,
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, 'productos_por_categoria.html', contexto)

def buscar(request):
    """Vista de Búsqueda"""
    query = request.GET.get('q', '')
    productos = Producto.objects.all()
    
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(fabricante__icontains=query)
        )
    
    opciones_filtro = obtener_opciones_filtro()
    
    contexto = {
        'categoria_actual': f'Resultados para: "{query}"',
        'productos_destacados': productos,
        'opciones_filtro': opciones_filtro,
        'query': query,
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, 'productos_por_categoria.html', contexto)

# ==============================================================================
# 2. LÓGICA DEL CARRITO (Añadir, Quitar, Ver)
# ==============================================================================

def obtener_cesta_actual(request):
    """Obtiene la cesta del usuario autenticado o de la sesión."""
    cesta = None
    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=usuario_cliente)
        except UsuarioCliente.DoesNotExist:
             cesta = None 
    else:
        session_id = request.session.get("cesta_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["cesta_id"] = session_id
            
        cesta, _ = CestaCompra.objects.get_or_create(session_id=session_id)
        
    return cesta

@require_POST
@transaction.atomic 
def update_cart(request, producto_id):
    """
    Gestiona los botones (+) y (-) del carrito.
    SOLO VALIDA disponibilidad. NO RESTA STOCK de la base de datos hasta el pago.
    """
    producto = get_object_or_404(Producto, id=producto_id)
    cesta = obtener_cesta_actual(request)
    
    item, created = ItemCestaCompra.objects.get_or_create(
        cesta_compra=cesta, 
        producto_id=producto_id, 
        defaults={'cantidad': 0, 'precio_unitario': producto.precio}
    )
    
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    action = request.POST.get('action')
    
    if is_ajax and not action:
        action = 'add'

    json_response_data = {'success': False, 'mensaje': 'Error'}

    # --- AÑADIR ---
    if action == 'add':
        try:
            cantidad_add = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad_add = 1

        if cantidad_add < 1:
            mensaje = "Debes seleccionar al menos 1 unidad."
            if is_ajax: return JsonResponse({'success': False, 'mensaje': mensaje})
            messages.error(request, mensaje)
            return redirect('carrito:carrito')

        if cantidad_add > producto.stock:
            mensaje = "Stock insuficiente para la cantidad solicitada."
            if is_ajax: return JsonResponse({'success': False, 'mensaje': mensaje})
            messages.error(request, mensaje)
        else:
            if item.cantidad + cantidad_add <= producto.stock:
                item.cantidad += cantidad_add
                item.save()      
                json_response_data = {
                    'success': True, 
                    'mensaje': 'Producto añadido',
                    'total_items': sum(i.cantidad for i in cesta.items.all()),
                    'nuevo_stock': producto.stock
                }
            else: 
                mensaje = "No puedes añadir más unidades; has alcanzado el límite de stock disponible."
                if is_ajax: return JsonResponse({'success': False, 'mensaje': mensaje})

    # --- QUITAR ---
    elif action == 'remove':
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
            json_response_data = {'success': True, 'mensaje': 'Cantidad reducida'}
        else:
            item.delete()
            json_response_data = {'success': True, 'mensaje': 'Producto eliminado del carrito'}

    if is_ajax:
        return JsonResponse(json_response_data)
    else:
        return redirect('carrito:carrito')

@require_POST
@transaction.atomic
def remove_from_cart(request, producto_id):
    cesta = obtener_cesta_actual(request)
    if not cesta: return redirect('carrito:carrito') 
    try:
        item = ItemCestaCompra.objects.get(cesta_compra=cesta, producto_id=producto_id)
        item.delete()
        messages.success(request, "Producto eliminado del carrito.")
    except ItemCestaCompra.DoesNotExist:
        pass 
    return redirect('carrito:carrito')

def ver_cesta(request):
    """Muestra la cesta."""
    items = []
    articulos_para_plantilla = []
    subtotal = Decimal('0.00')
    total = Decimal('0.00')
    cesta = obtener_cesta_actual(request)

    if cesta:
        items = cesta.items.all()
        for item in items:
            precio_unitario = item.producto.precio_rebajado if (hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado) else item.producto.precio
            precio_linea = precio_unitario * item.cantidad
            subtotal += precio_linea
            
            imagen_url = item.producto.imagen.url if (item.producto.imagen and item.producto.imagen.name) else "https://res.cloudinary.com/djfgts1ii/image/upload/imagen1_zi2acs.jpg"
                
            articulos_para_plantilla.append({
                    'id': item.producto.id, 
                    'nombre': item.producto.nombre,
                    'imagen_url': imagen_url,
                    'precio_unidad': precio_unitario,
                    'cantidad': item.cantidad,
                    'precio_total': precio_linea,
                    'stock': item.producto.stock,
            })
        total = subtotal 
    
    opciones_filtro = obtener_opciones_filtro()
    productos_destacados = Producto.objects.filter(stock__gt=0).order_by('?')[:5]

    context = {
        'articulos': articulos_para_plantilla, 
        'subtotal': f"{subtotal:.2f}",
        'total': f"{total:.2f}", 
        'opciones_filtro': opciones_filtro, 
        'productos_destacados': productos_destacados,
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, "carrito.html", context)

def vaciar_cesta(request):
    cesta = obtener_cesta_actual(request)
    if not cesta:
        messages.info(request, "No hay una cesta activa para vaciar.")
        return redirect('carrito:carrito')
    cesta.items.all().delete()
    messages.success(request, "La cesta ha sido vaciada correctamente.")
    return redirect('carrito:carrito')

# ==============================================================================
# 3. PROCESO DE PAGO Y VERIFICACIÓN DE STOCK
# ==============================================================================

def checkout(request):
    """
    Página de Pago.
    INCLUYE 'PORTERO': Verifica stock antes de dejarte ver el formulario.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('carrito:carrito')

    # --- PORTERO DE SEGURIDAD ---
    problema_detectado = False
    for item in cesta.items.select_related('producto'):
        stock_real = item.producto.stock
        if stock_real <= 0:
            messages.error(request, f"❌ El producto '{item.producto.nombre}' se acaba de agotar y ha sido eliminado.")
            item.delete()
            problema_detectado = True
        elif item.cantidad > stock_real:
            messages.warning(request, f"⚠️ Solo quedan {stock_real} unidades de '{item.producto.nombre}'. Hemos ajustado tu cesta.")
            item.cantidad = stock_real
            item.save()
            problema_detectado = True

    if problema_detectado:
        return redirect('carrito:carrito')
    # -----------------------------

    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        precio = item.producto.precio_rebajado if (hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado) else item.producto.precio
        subtotal += precio * item.cantidad
        
    coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
    total_inicial = subtotal + coste_envio
    
    # Pre-rellenar datos cliente
    datos_cliente = {
        'nombre': request.user.nombre if request.user.is_authenticated else '', 
        'apellidos': request.user.apellidos if request.user.is_authenticated else '',
        'email': request.user.corre_electronico if request.user.is_authenticated else '',
        'telefono': '', 'direccion_calle': '', 'direccion_cp': '', 'direccion_ciudad': '', 'direccion_pais': '',      
        'tipo_envio_default': TipoEnvio.DOMICILIO, 'tipo_pago_default': TipoPago.PASARELA_PAGO,
    }
    tarjetas_para_contexto = []

    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            datos_cliente['telefono'] = usuario_cliente.telefono or ''
            if usuario_cliente.direccion_envio:
                partes = [p.strip() for p in usuario_cliente.direccion_envio.split(',')]
                if len(partes) >= 3:
                    datos_cliente['direccion_calle'] = partes[0]
                    datos_cliente['direccion_pais'] = partes[-1]
                    datos_cliente['direccion_cp'] = partes[1]
                    datos_cliente['direccion_ciudad'] = partes[2]
            
            # Tarjetas
            for tarjeta in usuario_cliente.tarjetas.all():
                tarjetas_para_contexto.append({
                    'id': tarjeta.id,
                    'numero_enmascarado': f"************{tarjeta.ultimos_cuatro}",
                    'ultimos_cuatro': tarjeta.ultimos_cuatro,
                    'fecha_expiracion': tarjeta.card_expiry, 
                    'es_seleccionada': False 
                })
                
            if usuario_cliente.tipo_envio == TipoEnvio.RECOGIDA_TIENDA: coste_envio = Decimal('0.00')
            else: coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
            total_inicial = subtotal + coste_envio
        except UsuarioCliente.DoesNotExist:
            pass
    
    opciones_filtro = obtener_opciones_filtro()

    context = {
        'articulos': cesta.items.all(), 
        'subtotal': f"{subtotal:.2f}",
        'coste_envio': coste_envio,
        'total': f"{total_inicial:.2f}", 
        'datos_cliente': datos_cliente,
        'tarjetas_para_contexto': tarjetas_para_contexto, 
        'opciones_filtro': opciones_filtro, 
        'precio_seleccionado': '', 'fabricante_seleccionado': '', 'seccion_filtro_seleccionada': '',
    }
    return render(request, "pago.html", context)

@require_POST
@transaction.atomic 
def procesar_pago(request):
    """
    1. Verifica stock y limpia.
    2. Cobra y RESTA stock.
    """
    cesta = obtener_cesta_actual(request)
    if not cesta or not cesta.items.exists():
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito:carrito')

    # 1. FASE DE LIMPIEZA
    cesta_modificada = False
    for item in cesta.items.select_related('producto'):
        producto = item.producto
        stock_real = producto.stock
        if stock_real <= 0:
            messages.error(request, f"❌ El producto '{producto.nombre}' se ha agotado y se ha retirado.")
            item.delete()
            cesta_modificada = True
        elif item.cantidad > stock_real:
            messages.warning(request, f"⚠️ El stock de '{producto.nombre}' ha cambiado. Ajustado a {stock_real}.")
            item.cantidad = stock_real
            item.save()
            cesta_modificada = True

    if cesta_modificada: return redirect('carrito:carrito')

    # 2. PROCESAMIENTO
    entrega_value = request.POST.get('shipping_option') 
    payment_method_value = request.POST.get('payment_method') 
    email = request.POST.get('contact_email') 
    telefon = request.POST.get('contact_phone') 
    
    calle = (request.POST.get('address_street') or '').strip()
    ciudad = (request.POST.get('address_city') or '').strip()
    cpi = (request.POST.get('address_zip') or '').strip()
    pais = (request.POST.get('address_country') or '').strip()
    
    direccion = f"{calle}, {cpi} {ciudad}, {pais}"
    
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        precio = item.producto.precio_rebajado if (hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado) else item.producto.precio
        subtotal += precio * item.cantidad

    coste_entrega = Decimal('0.00')
    metodo_envio = TipoEnvio.DOMICILIO
    direccion_final = direccion

    if entrega_value == 'standard':
        if subtotal < 50: coste_entrega = Decimal('5.00')
        if not calle: 
            messages.error(request, "Dirección obligatoria para envío a domicilio.")
            return redirect('carrito:checkout')
    elif entrega_value == 'express':
        metodo_envio = TipoEnvio.RECOGIDA_TIENDA
        direccion_final = "Calle Jardines del Guadalquivir, 45, 41012 Sevilla" 
    
    metodo_pago = TipoPago.PASARELA_PAGO if payment_method_value == 'gateway' else TipoPago.CONTRAREEMBOLSO
    pago = (metodo_pago == TipoPago.PASARELA_PAGO)
    total_importe = subtotal + coste_entrega
    
    usuario_cliente = None
    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            if entrega_value == 'standard':
                usuario_cliente.direccion_envio = direccion_final
            usuario_cliente.save()
        except UsuarioCliente.DoesNotExist: pass
            
    try:
        pedido = Pedido.objects.create(
            usuario_cliente=usuario_cliente, estado=EstadoPedido.PEDIDO, 
            subtotal_importe=subtotal, coste_entrega=coste_entrega, total_importe=total_importe,
            metodo_pago=metodo_pago, tipo_envio=metodo_envio, direccion_envio=direccion_final, 
            correo_electronico=email, telefono=telefon, pago=pago,
        )

        for item_cesta in cesta.items.select_related('producto'):
            producto = item_cesta.producto
            if item_cesta.cantidad > producto.stock: raise ValueError("Stock insuficiente.") 
            
            precio_final = producto.precio_rebajado if (hasattr(producto, 'precio_rebajado') and producto.precio_rebajado) else producto.precio
            ItemPedido.objects.create(pedido=pedido, producto=producto, cantidad=item_cesta.cantidad, precio_unitario=precio_final)
            
            # RESTA DE STOCK REAL
            producto.stock -= item_cesta.cantidad
            producto.save()

        # Email
        try:
            pedido.refresh_from_db()
            tracking_url = request.build_absolute_uri(reverse('seguimiento_pedido', kwargs={'order_id': pedido.id, 'tracking_hash': pedido.tracking_id}))
            items_email = pedido.items.select_related('producto').all()
            contexto = {'pedido': pedido, 'items': items_email, 'tracking_url': tracking_url}
            
            subject = f"Confirmación pedido #{pedido.id}"
            text_body = f"Gracias. Sigue tu pedido aquí: {tracking_url}"
            html_body = render_to_string('correo.html', contexto) # Requiere template 'correo.html'

            msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        except Exception: pass

        cesta.items.all().delete()
        request.session['ultimo_correo_pedido'] = email
        messages.success(request, f"🛒 ¡Pedido #{pedido.id} realizado con éxito!")
        return redirect('carrito:fin_compra')
        
    except ValueError:
        transaction.set_rollback(True)
        return redirect('carrito:carrito')

def compra_finalizada(request):
    """Muestra confirmación."""
    correo = request.session.pop('ultimo_correo_pedido', '')
    return render(request, 'compra_finalizada.html', {'correo': correo, 'opciones_filtro': obtener_opciones_filtro()})

# --- API ---
def verificar_stock_api(request):
    """API para polling de stock."""
    ids_param = request.GET.get('ids', '')
    if not ids_param: return JsonResponse({})
    try:
        p_ids = [int(x) for x in ids_param.split(',') if x.isdigit()]
    except ValueError: return JsonResponse({})
    
    productos = Producto.objects.filter(id__in=p_ids)
    return JsonResponse({str(p.id): p.stock for p in productos})