from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from decimal import Decimal
from django.contrib import messages
import uuid
from django.db import transaction
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.urls import reverse
from django.conf import settings

# Importaciones de modelos unificadas
from home.models import (
    Producto, CestaCompra, UsuarioCliente, ItemCestaCompra,
    Pedido, ItemPedido, TipoPago, TipoEnvio, EstadoPedido, Tarjeta
)

# Importación de vistas auxiliares (filtros)
from home.views import obtener_opciones_filtro

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
    
    # Detectar AJAX
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    action = request.POST.get('action')
    
    if is_ajax and not action:
        action = 'add'

    json_response_data = {'success': False, 'mensaje': 'Error'}

    # =========================================================
    # ACCIÓN: AÑADIR (Botón + o "Añadir a Cesta")
    # =========================================================
    if action == 'add':
        try:
            cantidad_add = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad_add = 1

        # 1. Validación: Cantidad mínima
        if cantidad_add < 1:
            mensaje = "Debes seleccionar al menos 1 unidad."
            if is_ajax:
                return JsonResponse({'success': False, 'mensaje': mensaje})
            messages.error(request, mensaje)
            return redirect('carrito:carrito')

        # 2. Validación: Stock suficiente GLOBAL (sin decir el número exacto)
        if cantidad_add > producto.stock:
            mensaje = "Stock insuficiente para la cantidad solicitada."
            
            if is_ajax:
                return JsonResponse({'success': False, 'mensaje': mensaje})
            messages.error(request, mensaje)
            
        else:
            # 3. Validación: Stock suficiente sumando lo que ya tienes en el carrito
            if item.cantidad + cantidad_add <= producto.stock:
                item.cantidad += cantidad_add
                item.save()      
                # NOTA: No hacemos producto.save() aquí. El stock se mantiene reservado visualmente pero no en BD.
                
                json_response_data = {
                    'success': True, 
                    'mensaje': 'Producto añadido',
                    'total_items': sum(i.cantidad for i in cesta.items.all()),
                    'nuevo_stock': producto.stock
                }
            else: 
                # Mensaje genérico
                mensaje = "No puedes añadir más unidades; has alcanzado el límite de stock disponible."
                
                if is_ajax:
                    return JsonResponse({'success': False, 'mensaje': mensaje})

    # =========================================================
    # ACCIÓN: QUITAR (Botón -)
    # =========================================================
    elif action == 'remove':
        
        # Como no restamos stock al añadir, no hace falta devolverlo al quitar.
        # Solo gestionamos la línea del carrito.
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
            json_response_data = {'success': True, 'mensaje': 'Cantidad reducida'}
        else:
            # Si la cantidad era 1 y restamos 1, se borra el item
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
    if not cesta:
        return redirect('carrito:carrito') 

    try:
        # Buscamos el producto en el carrito
        item = ItemCestaCompra.objects.get(cesta_compra=cesta, producto_id=producto_id)
        
        # Borramos el item del carrito (El stock no se toca porque nunca se restó)
        item.delete()
        
        messages.success(request, "Producto eliminado del carrito.")
        
    except ItemCestaCompra.DoesNotExist:
        pass 

    return redirect('carrito:carrito')

def ver_cesta(request):
    """
    Muestra la cesta unificada para todos los usuarios.
    """
    items = []
    articulos_para_plantilla = []
    subtotal = Decimal('0.00')
    total = Decimal('0.00')

    cesta = None

    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            cesta, creada = CestaCompra.objects.get_or_create(usuario_cliente=usuario_cliente)
        except UsuarioCliente.DoesNotExist:
             cesta = None
    else:
        session_id = request.session.get("cesta_id")
        if session_id:
            cesta = CestaCompra.objects.filter(session_id=session_id).first()
        else:
            cesta = None

    if cesta:
        items = cesta.items.all()
        for item in items:
            
            # 1. Determinamos precio (oferta vs normal)
            if hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado:
                precio_unitario = item.producto.precio_rebajado
            else:
                precio_unitario = item.producto.precio

            # 2. Calculamos precio de línea
            precio_linea = precio_unitario * item.cantidad
            subtotal += precio_linea
                
            if item.producto.imagen and item.producto.imagen.name:
                imagen_url = item.producto.imagen.url
            else:
                imagen_url = "https://res.cloudinary.com/djfgts1ii/image/upload/imagen1_zi2acs.jpg"
                
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

    # Productos sugeridos
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
    """
    Vacía los items de la cesta actual.
    """
    cesta = obtener_cesta_actual(request)
    if not cesta:
        messages.info(request, "No hay una cesta activa para vaciar.")
        return redirect('carrito:carrito')

    # Borrar los items asociados a la cesta
    cesta.items.all().delete()

    # Limpiar identificador de sesión
    try:
        if 'cesta_id' in request.session:
            del request.session['cesta_id']
    except Exception:
        pass

    messages.success(request, "La cesta ha sido vaciada correctamente.")
    return redirect('carrito:carrito')

def checkout(request):
    """
    Vista que muestra la página de pago (GET).
    INCLUYE BLOQUEO DE SEGURIDAD: Si no hay stock, te devuelve al carrito.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect('carrito:carrito')

    # ==============================================================================
    # 🛡️ EL PORTERO: Validar stock ANTES de dejar entrar al pago
    # ==============================================================================
    problema_detectado = False

    for item in cesta.items.select_related('producto'):
        stock_real = item.producto.stock
        
        # 1. Si el producto se ha quedado a 0 (Agotado total)
        if stock_real <= 0:
            messages.error(request, f"❌ ¡Lo sentimos! El producto '{item.producto.nombre}' se acaba de agotar y ha sido eliminado de tu cesta.")
            item.delete()
            problema_detectado = True
            
        # 2. Si pides más de lo que queda (ej: pides 5, quedan 2)
        elif item.cantidad > stock_real:
            messages.warning(request, f"⚠️ Solo quedan {stock_real} unidades de '{item.producto.nombre}'. Hemos ajustado tu cesta.")
            item.cantidad = stock_real
            item.save()
            problema_detectado = True

    # Si el portero encontró problemas, TE DEVUELVE AL CARRITO. No entras al pago.
    if problema_detectado:
        return redirect('carrito:carrito')
    # ==============================================================================

    # --- SI LLEGAMOS AQUÍ, TODO ESTÁ CORRECTO ---
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        if hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado:
            precio = item.producto.precio_rebajado
        else:
            precio = item.producto.precio
        subtotal += precio * item.cantidad
        
    coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
    total_inicial = subtotal + coste_envio
    
    tarjetas_para_contexto = []

    datos_cliente = {
        'nombre': '', 'apellidos': '', 'email': '', 'telefono': '',
        'direccion_calle': '', 'direccion_cp': '', 'direccion_ciudad': '', 'direccion_pais': '',      
        'tipo_envio_default': TipoEnvio.DOMICILIO,        
        'tipo_pago_default': TipoPago.PASARELA_PAGO,
    }

    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            tarjetas_guardadas = usuario_cliente.tarjetas.all()
            
            # Enmascarar tarjetas
            for tarjeta in tarjetas_guardadas:
                tarjetas_para_contexto.append({
                    'id': tarjeta.id,
                    'numero_enmascarado': f"************{tarjeta.ultimos_cuatro}",
                    'ultimos_cuatro': tarjeta.ultimos_cuatro,
                    'fecha_expiracion': tarjeta.card_expiry, 
                    'es_seleccionada': (tarjeta == tarjetas_guardadas.first()) 
                })
            
            # Rellenar datos básicos
            datos_cliente['nombre'] = request.user.nombre 
            datos_cliente['apellidos'] = request.user.apellidos
            datos_cliente['email'] = request.user.corre_electronico
            datos_cliente['telefono'] = usuario_cliente.telefono if usuario_cliente.telefono and str(usuario_cliente.telefono) != 'None' else ''
            
            # Lógica de desglose de dirección
            direccion_completa = usuario_cliente.direccion_envio
            if direccion_completa and str(direccion_completa) != 'None':
                partes = [p.strip() for p in direccion_completa.split(',')]
                if len(partes) >= 4:
                    datos_cliente['direccion_calle'] = f"{partes[0]}, {partes[1]}"
                    datos_cliente['direccion_pais'] = partes[-1]
                    cp_ciudad_raw = partes[-2] 
                    cp_ciudad_split = cp_ciudad_raw.split(' ', 1)
                    if len(cp_ciudad_split) >= 2:
                        datos_cliente['direccion_cp'] = cp_ciudad_split[0]
                        datos_cliente['direccion_ciudad'] = cp_ciudad_split[1]
                        
                elif len(partes) == 3:
                    datos_cliente['direccion_calle'] = partes[0]
                    datos_cliente['direccion_pais'] = partes[-1]
                    cp_ciudad_split = partes[1].split(' ', 1)
                    if len(cp_ciudad_split) >= 2:
                        datos_cliente['direccion_cp'] = cp_ciudad_split[0]
                        datos_cliente['direccion_ciudad'] = cp_ciudad_split[1]

            datos_cliente['tipo_envio_default'] = usuario_cliente.tipo_envio 
            datos_cliente['tipo_pago_default'] = usuario_cliente.tipo_pago

            # Recalcular envío según preferencia
            if usuario_cliente.tipo_envio == TipoEnvio.RECOGIDA_TIENDA:
                coste_envio = Decimal('0.00')
            else:
                coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
                
        except UsuarioCliente.DoesNotExist:
            pass
    
    total_inicial = subtotal + coste_envio
    opciones_filtro = obtener_opciones_filtro()

    context = {
        'articulos': cesta.items.all(), 
        'subtotal': f"{subtotal:.2f}",
        'coste_envio': coste_envio,
        'total': f"{total_inicial:.2f}", 
        'datos_cliente': datos_cliente,
        'tarjetas_para_contexto': tarjetas_para_contexto, 
        'tiene_tarjeta_guardada': bool(tarjetas_para_contexto), 
        'opciones_filtro': opciones_filtro, 
        
        # Filtros vacíos
        'precio_seleccionado': '', 'fabricante_seleccionado': '', 'seccion_filtro_seleccionada': '',
    }
    
    return render(request, "pago.html", context)

@require_POST
@transaction.atomic 
def procesar_pago(request):
    """
    1. Verifica stock y CORRIGE la cesta si falta algo (elimina o ajusta cantidad).
    2. Si todo está bien, procesa el pago y crea el pedido.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito:carrito')

    # ==============================================================================
    # 1. FASE DE LIMPIEZA: Verificar Stock antes de procesar nada
    # ==============================================================================
    cesta_modificada = False

    for item in cesta.items.select_related('producto'):
        producto = item.producto
        stock_real = producto.stock
        
        # CASO A: El producto se ha quedado a 0 (Alguien compró el último)
        if stock_real <= 0:
            messages.error(request, f"❌ El producto '{producto.nombre}' se ha agotado y se ha retirado de tu cesta.")
            item.delete()
            cesta_modificada = True
            
        # CASO B: Hay stock, pero menos del que el usuario pide
        elif item.cantidad > stock_real:
            messages.warning(request, f"⚠️ El stock de '{producto.nombre}' ha cambiado. Hemos ajustado la cantidad a {stock_real} unidades.")
            item.cantidad = stock_real
            item.save()
            cesta_modificada = True

    # Si hubo algún cambio (borrado o ajuste), devolvemos al usuario al carrito para que lo vea
    if cesta_modificada:
        return redirect('carrito:carrito')

    # ==============================================================================
    # 2. FASE DE PROCESAMIENTO (Si llegamos aquí, el stock es correcto)
    # ==============================================================================
    
    # Recoger datos del formulario
    entrega_value = request.POST.get('shipping_option') 
    payment_method_value = request.POST.get('payment_method') 
    email = request.POST.get('contact_email') 
    telefon = request.POST.get('contact_phone') 
    
    calle = request.POST.get('direccion_calle')
    ciudad = request.POST.get('direccion_ciudad')
    cpi = request.POST.get('direccion_cp')      
    pais = request.POST.get('direccion_pais')    
    
    # Datos Tarjeta
    calle = (request.POST.get('address_street') or request.POST.get('direccion_calle') or '').strip()
    ciudad = (request.POST.get('address_city') or request.POST.get('direccion_ciudad') or '').strip()
    cpi = (request.POST.get('address_zip') or request.POST.get('direccion_cp') or '').strip()
    pais = (request.POST.get('address_country') or request.POST.get('direccion_pais') or '').strip()
    
    card_number = request.POST.get('card_number')
    expiry_date = request.POST.get('expiry_date') 
    card_cvv = request.POST.get('cvv') 
    save_card_flag = request.POST.get('save_card') == 'on'
    
    direccion = f"{calle}, {cpi} {ciudad}, {pais}"
    partes = []
    if calle.strip(): partes.append(calle.strip())
    cp_ciudad = ' '.join(p for p in (cpi.strip(), ciudad.strip()) if p)
    if cp_ciudad: partes.append(cp_ciudad)
    if pais.strip(): partes.append(pais.strip())
    direccion = ', '.join(partes)

    # Calcular Subtotal
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        if hasattr(item.producto, 'precio_rebajado') and item.producto.precio_rebajado:
            precio = item.producto.precio_rebajado
        else:
            precio = item.producto.precio
        subtotal += precio * item.cantidad

    coste_entrega = Decimal('0.00')
    
    # Lógica de Envío
    if entrega_value == 'standard':
        metodo_envio = TipoEnvio.DOMICILIO
        if subtotal < 50:
            coste_entrega = Decimal('5.00')
        else:
            coste_entrega = Decimal('0.00')
        direccion_final = direccion
        direccion_final = direccion or ''
            
    elif entrega_value == 'express':
        metodo_envio = TipoEnvio.RECOGIDA_TIENDA
        coste_entrega = Decimal('0.00') 
        direccion_final = "Calle Jardines del Guadalquivir, 45, 41012 Sevilla, España" 
    else:
        messages.error(request, "Opción de envío no válida.")
        return redirect('carrito:checkout')

    # Lógica de Pago
    if metodo_envio == TipoEnvio.DOMICILIO and not direccion_final:
        messages.error(request, "Debe proporcionar una dirección válida para el envío a domicilio.")
        return redirect('carrito:checkout')

    if payment_method_value == 'cash': 
        metodo_pago = TipoPago.CONTRAREEMBOLSO
        pago = False 
    elif payment_method_value == 'gateway': 
        metodo_pago = TipoPago.PASARELA_PAGO
        pago = True 
    else: 
        messages.error(request, "Opción de pago no válida.")
        return redirect('carrito:checkout')
    
    total_importe = subtotal + coste_entrega
    
    usuario_cliente = None
    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            
            # Actualizar perfil con los nuevos datos
            usuario_cliente.direccion_envio = direccion_final if metodo_envio == TipoEnvio.DOMICILIO else usuario_cliente.direccion_envio
            usuario_cliente.tipo_envio = metodo_envio
            usuario_cliente.tipo_pago = metodo_pago
            usuario_cliente.telefono = telefon 
            usuario_cliente.save()

            # Guardar tarjeta si el usuario lo pidió
            if metodo_pago == TipoPago.PASARELA_PAGO and save_card_flag and card_number and expiry_date and card_cvv:
                nueva_tarjeta = Tarjeta(usuario_cliente=usuario_cliente)
                nueva_tarjeta.set_card_details(card_number, expiry_date, card_cvv)
                try:
                    nueva_tarjeta.save()
                    messages.info(request, f"💳 Tarjeta guardada correctamente.")
                except Exception:
                    pass # Ya existía
            
        except UsuarioCliente.DoesNotExist:
            pass # Usuario sin perfil cliente (raro pero posible)
            
    # --- CREAR PEDIDO ---
    try:
        pedido = Pedido.objects.create(
            usuario_cliente=usuario_cliente,
            estado=EstadoPedido.PEDIDO, 
            subtotal_importe=subtotal,
            coste_entrega=coste_entrega, 
            total_importe=total_importe,
            metodo_pago=metodo_pago,
            tipo_envio=metodo_envio, 
            direccion_envio=direccion_final, 
            correo_electronico=email,
            telefono=telefon,
            pago=pago,
        )

        for item_cesta in cesta.items.select_related('producto'):
            producto = item_cesta.producto
            
            # 1. Comprobación final de stock antes de confirmar (por si acaso)
            if item_cesta.cantidad > producto.stock:
                 messages.error(request, f"Stock insuficiente en '{producto.nombre}' durante el procesamiento. Inténtalo de nuevo.")
                 raise ValueError("Stock insuficiente.") 
            
            # Precio final para el historial
            if hasattr(producto, 'precio_rebajado') and producto.precio_rebajado:
                precio_unitario_final = producto.precio_rebajado
            else:
                precio_unitario_final = producto.precio

            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item_cesta.cantidad,
                precio_unitario=precio_unitario_final,
            )
            
            # 2. RESTA DE STOCK (AQUÍ ES DONDE SE RESTA REALMENTE)
            producto.stock -= item_cesta.cantidad
            producto.save()

        # Enviar correo confirmación
        try:
            tracking_url = request.build_absolute_uri(reverse('seguimiento_pedido', args=[pedido.id, pedido.tracking_id]))
            subject = f"Confirmación pedido #{pedido.id}"
            text_body = f"Gracias por tu pedido #{pedido.id}. Puedes seguirlo en: {tracking_url}"
            html_body = f"<p>Gracias por tu pedido <strong>#{pedido.id}</strong>.</p><p><a href=\"{tracking_url}\">Ver seguimiento</a></p>"

            msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        except Exception:
            messages.warning(request, "Pedido realizado, pero no se pudo enviar el correo de confirmación.")

        # Limpieza final
        cesta.items.all().delete()
        request.session['ultimo_correo_pedido'] = email

        messages.success(request, f"🛒 ¡Pedido #{pedido.id} realizado con éxito!")
        return redirect('carrito:fin_compra')
        
    except ValueError:
        # Si hubo error de stock, deshacer cambios en BD
        transaction.set_rollback(True)
        return redirect('carrito:carrito')
    
def compra_finalizada(request):
    """Muestra confirmación post-compra."""
    correo_pedido = request.session.pop('ultimo_correo_pedido', '')
    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'mensaje_final': '¡Gracias por tu compra! Tu pedido ha sido procesado con éxito.',
        'correo': correo_pedido,
        'opciones_filtro': opciones_filtro, 
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, 'compra_finalizada.html', contexto)

# --- API DE STOCK (PARA JAVASCRIPT) ---

def verificar_stock_api(request):
    """
    Recibe una lista de IDs (ej: ?ids=1,5,8) y devuelve su stock actual en JSON.
    """
    ids_param = request.GET.get('ids', '')
    if not ids_param:
        return JsonResponse({})
    
    # Convertimos "1,5,8" en una lista de enteros [1, 5, 8]
    try:
        product_ids = [int(id_str) for id_str in ids_param.split(',') if id_str.isdigit()]
    except ValueError:
        return JsonResponse({})

    # Consultamos la base de datos
    productos = Producto.objects.filter(id__in=product_ids)
    
    # Creamos un diccionario: { "1": 10, "5": 0, "8": 3 }
    data = {str(p.id): p.stock for p in productos}
    
    return JsonResponse(data)