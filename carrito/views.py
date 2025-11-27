from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse  # <--- IMPORTANTE: Necesario para la Home
from home.models import Producto 
from decimal import Decimal 
from django.contrib import messages
from home.models import (
    Producto, CestaCompra, UsuarioCliente, ItemCestaCompra,
    Pedido, ItemPedido, TipoPago, TipoEnvio, EstadoPedido, Tarjeta
)

import uuid 
from django.db import transaction

# Asegúrate de que esta importación sea correcta según tu estructura
from home.views import obtener_opciones_filtro
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.urls import reverse
from django.conf import settings

def obtener_cesta_actual(request):
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
@transaction.atomic  # Esto asegura que la base de datos no falle a medias
def update_cart(request, producto_id):
    """
    Gestiona los botones (+) y (-) del carrito.
    Resta stock al añadir y devuelve stock al quitar.
    """
    producto = get_object_or_404(Producto, id=producto_id)
    cesta = obtener_cesta_actual(request)
    
    # Obtenemos o creamos el item
    item, created = ItemCestaCompra.objects.get_or_create(
        cesta_compra=cesta, 
        producto_id=producto_id, 
        defaults={'cantidad': 0, 'precio_unitario': producto.precio}
    )
    
    # Detectar AJAX
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    action = request.POST.get('action')
    
    # Si viene por AJAX sin acción, asumimos añadir 1
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

        # 1. Comprobamos si hay stock real suficiente
        if cantidad_add > producto.stock:
            mensaje = f"Solo quedan {producto.stock} unidades disponibles."
            if is_ajax:
                return JsonResponse({'success': False, 'mensaje': mensaje})
            messages.error(request, mensaje)
            
        else:
            # 2. RESTAMOS el stock y AUMENTAMOS el carrito
            producto.stock -= cantidad_add
            producto.save()  # <--- Guardamos el cambio de stock
            
            item.cantidad += cantidad_add
            item.save()      # <--- Guardamos el cambio en el carrito
            
            json_response_data = {
                'success': True, 
                'mensaje': 'Producto añadido',
                'total_items': sum(i.cantidad for i in cesta.items.all()),
                'nuevo_stock': producto.stock
            }

    # =========================================================
    # ACCIÓN: QUITAR (Botón -)
    # =========================================================
    elif action == 'remove':
        # Al pulsar el botón menos (-), SIEMPRE devolvemos 1 al stock
        producto.stock += 1
        producto.save()  # <--- El stock vuelve a la tienda

        # Ahora gestionamos el carrito
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
        
        # ===========================================================
        # 🔴 PASO CLAVE: ANTES DE BORRAR, DEVOLVEMOS EL STOCK 🔴
        # ===========================================================
        producto = item.producto
        producto.stock += item.cantidad  # <--- Devuelve TODAS las unidades a la tienda
        producto.save()                  # <--- Guarda el cambio en la base de datos
        
        # Ahora sí, borramos el item del carrito
        item.delete()
        
        messages.success(request, "Producto eliminado y stock restaurado.")
        
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
            # Asegurarnos de que precio_linea siempre esté definido (evita errores cuando stock == 0)
            precio_linea = Decimal('0.00')
            precio_linea = item.producto.precio * item.cantidad
            subtotal += precio_linea
                
            if item.producto.imagen and item.producto.imagen.name:
                imagen_url = item.producto.imagen.url
            else:
                imagen_url = "https://res.cloudinary.com/djfgts1ii/image/upload/imagen1_zi2acs.jpg"
                
            articulos_para_plantilla.append({
                'id': item.producto.id, 
                'nombre': item.producto.nombre,
                'imagen_url': imagen_url,
                'precio_unidad': item.producto.precio,
                'cantidad': item.cantidad,
                'precio_total': precio_linea,
                'stock': item.producto.stock,
        })
        total = subtotal 
    
    opciones_filtro = obtener_opciones_filtro()

    # --- NUEVO: Obtener productos sugeridos para el carrusel de abajo ---
    # Cogemos 5 productos aleatorios con stock
    productos_destacados = Producto.objects.filter(stock__gt=0).order_by('?')[:5]

    context = {
        'articulos': articulos_para_plantilla, 
        'subtotal': f"{subtotal:.2f}",
        'total': f"{total:.2f}", 
        'opciones_filtro': opciones_filtro, 
        
        # --- NUEVO: Añadimos la variable al contexto ---
        'productos_destacados': productos_destacados,
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }

    return render(request, "carrito.html", context)


def vaciar_cesta(request):
    """
    Vacía los items de la cesta actual (para sesión o usuario autenticado)
    y limpia la sesión `cesta_id` para forzar la creación de una nueva cesta.
    """
    cesta = obtener_cesta_actual(request)
    if not cesta:
        messages.info(request, "No hay una cesta activa para vaciar.")
        return redirect('carrito:carrito')

    # Borrar los items asociados a la cesta pero conservar la fila de la cesta
    cesta.items.all().delete()

    # Limpiar identificador de sesión para evitar reaparecer la misma cesta
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
    Asegura que los totales y los artículos de la cesta se pasen a la plantilla.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "Tu carrito está vacío. Añade productos antes de pagar.")
        return redirect('carrito:carrito')
        
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        subtotal += item.producto.precio * item.cantidad
        
    coste_envio= Decimal('0.00')
    coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
 
    total_inicial = subtotal + coste_envio
    tarjetas_guardadas = None
    tarjetas_para_contexto = []
    

    datos_cliente = {
        'nombre': '', 
        'apellidos': '', 
        'email': '', 
        'telefono': '',
        'direccion_calle': '',     
        'direccion_cp': '',    
        'direccion_ciudad': '',
        'direccion_pais': '',      
        'tipo_envio_default': TipoEnvio.DOMICILIO,        
        'tipo_pago_default': TipoPago.PASARELA_PAGO,
    }

    if request.user.is_authenticated:
        try:
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
            tarjetas_guardadas = usuario_cliente.tarjetas.all()
            
            # 1. Procesar y enmascarar las tarjetas para el frontend
            for tarjeta in tarjetas_guardadas:
                # La tarjeta enmascarada tendrá 12 asteriscos + los 4 dígitos finales
                numero_enmascarado = f"************{tarjeta.ultimos_cuatro}"
                
                tarjetas_para_contexto.append({
                    'id': tarjeta.id,
                    'numero_enmascarado': numero_enmascarado,
                    'ultimos_cuatro': tarjeta.ultimos_cuatro,
                    'fecha_expiracion': tarjeta.card_expiry, # Pasa la fecha real (MM/AA)
                    'es_seleccionada': (tarjeta == tarjetas_guardadas.first()) # Marcar la primera por defecto
                })
            
            datos_cliente['nombre'] = request.user.nombre 
            datos_cliente['apellidos'] = request.user.apellidos
            datos_cliente['email'] = request.user.corre_electronico
            datos_cliente['telefono'] = usuario_cliente.telefono 
            
            direccion_completa = usuario_cliente.direccion_envio
            if direccion_completa:
                partes = [p.strip() for p in direccion_completa.split(',')]
                
                if len(partes) >= 4:
                    calle_completa = f"{partes[0]}, {partes[1]}"
                    datos_cliente['direccion_calle'] = calle_completa
                    
                    cp_ciudad_raw = partes[-2] 
                    
                    datos_cliente['direccion_pais'] = partes[-1]
                    
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

            # Recalcular costes según la preferencia guardada en el perfil
            if usuario_cliente.tipo_envio == TipoEnvio.RECOGIDA_TIENDA:
                coste_envio = Decimal('0.00')
            else:
                coste_envio = Decimal('5.00') if subtotal < 50 else Decimal('0.00')
                
            total_inicial = subtotal + coste_envio
            
        except UsuarioCliente.DoesNotExist:
            pass
    
    # Asegurar que el coste de envío sea un Decimal para el total final
    total_inicial = subtotal + coste_envio
    
    opciones_filtro = obtener_opciones_filtro()

    context = {
        'articulos': cesta.items.all(), 
        'subtotal': f"{subtotal:.2f}",
        'coste_envio': coste_envio,
        'total': f"{total_inicial:.2f}", 
        'datos_cliente': datos_cliente,
        'tarjetas_para_contexto': tarjetas_para_contexto, # La lista de tarjetas procesadas
        'tiene_tarjeta_guardada': bool(tarjetas_para_contexto), # True si la lista no está vacía
        'opciones_filtro': opciones_filtro, 
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto en home
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
        
    }
    
    return render(request, "pago.html", context)

@require_POST
@transaction.atomic 
def procesar_pago(request):
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "El carrito está vacío. No se puede procesar el pago.")
        return redirect('carrito:carrito')
        

    entrega_value = request.POST.get('shipping_option') 
    payment_method_value = request.POST.get('payment_method') 
    email = request.POST.get('contact_email') 
    telefon = request.POST.get('contact_phone') 
    
    # 📌 Capturar los cuatro campos de dirección separados del formulario POST
    # Compatibilidad: la plantilla `pago.html` usa `address_street`, `address_city`,
    # `address_zip`, `address_country`. Intentamos leer primero los nombres nuevos,
    # si no existen leemos los nombres antiguos.
    calle = (request.POST.get('address_street') or request.POST.get('direccion_calle') or '').strip()
    ciudad = (request.POST.get('address_city') or request.POST.get('direccion_ciudad') or '').strip()
    cpi = (request.POST.get('address_zip') or request.POST.get('direccion_cp') or '').strip()
    pais = (request.POST.get('address_country') or request.POST.get('direccion_pais') or '').strip()
    card_number = request.POST.get('card_number')
    expiry_date = request.POST.get('expiry_date') # MM/AA
    card_cvv = request.POST.get('cvv') #  CV
    # Flag para guardar tarjeta (solo presente si el usuario está autenticado)
    save_card_flag = request.POST.get('save_card') == 'on'
    # 📌 Volver a combinar la dirección para guardarla en el campo único del Pedido
    # Construimos la dirección de forma segura, omitiendo partes vacías
    partes = []
    if calle.strip():
        partes.append(calle.strip())
    cp_ciudad = ' '.join(p for p in (cpi.strip(), ciudad.strip()) if p)
    if cp_ciudad:
        partes.append(cp_ciudad)
    if pais.strip():
        partes.append(pais.strip())

    direccion = ', '.join(partes)

    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        subtotal += item.producto.precio * item.cantidad

    coste_entrega = Decimal('0.00')
    
    if entrega_value == 'standard':
        metodo_envio = TipoEnvio.DOMICILIO
        if subtotal < 50:
            coste_entrega = Decimal('5.00')
        else:
            coste_entrega = Decimal('0.00')
            
        # 📌 Usar la dirección combinada de los 4 campos si es Domicilio
        # Si no hay partes, mantener cadena vacía (no guardar 'None')
        direccion_final = direccion or ''
            
    elif entrega_value == 'express':
        metodo_envio = TipoEnvio.RECOGIDA_TIENDA
        coste_entrega = Decimal('0.00') 
        # Usar la dirección fija de la tienda si es Recogida
        direccion_final = "Calle Jardines del Guadalquivir, 45, 41012 Sevilla, España" 

    else:
        messages.error(request, "Opción de envío no válida.")
        return redirect('carrito:checkout')

    # Validación: si se selecciona Domicilio, la dirección no puede quedar vacía
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
            
            # 📌 Actualizar la dirección completa del perfil del cliente (si está autenticado)
            usuario_cliente.direccion_envio = direccion_final if metodo_envio == TipoEnvio.DOMICILIO else usuario_cliente.direccion_envio
            usuario_cliente.tipo_envio = metodo_envio
            usuario_cliente.tipo_pago = metodo_pago
            usuario_cliente.telefono = telefon # Actualizar teléfono si es necesario
            usuario_cliente.save()

            if metodo_pago == TipoPago.PASARELA_PAGO and save_card_flag and card_number and expiry_date and card_cvv:
                
                # Crear instancia del nuevo modelo
                nueva_tarjeta = Tarjeta(
                    usuario_cliente=usuario_cliente
                )
                
                # Hashear y asignar detalles (usa el método que definimos en models.py)
                nueva_tarjeta.set_card_details(card_number, expiry_date, card_cvv)
                
                # Intentar guardar, verificando si ya existe un hash idéntico para este usuario
                try:
                    nueva_tarjeta.save()
                    messages.info(request, f"💳 Tarjeta que termina en {nueva_tarjeta.ultimos_cuatro} guardada de forma segura.")
                except Exception:
                    # Si falla al guardar (unique_together error), significa que ya existe
                    messages.warning(request, "Esta tarjeta ya está guardada en su perfil.")
            
        except UsuarioCliente.DoesNotExist:
            messages.error(request, "Error: No se encontró el perfil de cliente asociado a su cuenta.")
            
    # 3. Crear el Pedido (Registro principal)
    try:
        pedido = Pedido.objects.create(
            usuario_cliente=usuario_cliente,
            estado=EstadoPedido.PEDIDO, 
            subtotal_importe=subtotal,
            coste_entrega=coste_entrega, 
            total_importe=total_importe,
            metodo_pago=metodo_pago,
            tipo_envio=metodo_envio, 
            direccion_envio=direccion_final, # Usar la dirección final (combinada o de la tienda)
            correo_electronico=email,
            telefono=telefon,
            pago=pago,
            tracking_id=uuid.uuid4().hex[:10].upper()
            
        )

        for item_cesta in cesta.items.select_related('producto'):
            producto = item_cesta.producto
            if item_cesta.cantidad > producto.stock:
                 messages.error(request, f"Lo sentimos, el stock de {producto.nombre} ha cambiado. Solo quedan {producto.stock} unidades.")
                 raise ValueError("Stock insuficiente.") 
            
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item_cesta.cantidad,
                precio_unitario=item_cesta.producto.precio,
            )

        # Enviar correo de confirmación (intentar, pero no romper la transacción si falla)
        try:
            # Asegurar que el pedido tiene el tracking_id más reciente
            pedido.refresh_from_db()
            tracking_url = request.build_absolute_uri(
                reverse('seguimiento_pedido', kwargs={'order_id': pedido.id, 'tracking_hash': pedido.tracking_id})
            )
            subject = f"Confirmación pedido #{pedido.id}"
            text_body = f"Gracias por tu pedido #{pedido.id}. Puedes seguir el pedido en: {tracking_url}"
            html_body = (
                f"<p>Gracias por tu pedido <strong>#{pedido.id}</strong>.</p>"
                f"<p>Puedes seguirlo aquí: <a href=\"{tracking_url}\">Ver seguimiento</a></p>"
            )

            msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error enviando email de confirmación: %s", e)
            messages.warning(request, "No se pudo enviar el email de confirmación. Igualmente, su pedido se ha procesado.")

        # 5. Vaciar Cesta
        cesta.items.all().delete()
        request.session['ultimo_correo_pedido'] = email

        messages.success(request, f"🛒 ¡Pedido #{pedido.id} realizado con éxito! Total a pagar: {total_importe:.2f} €")
        return redirect('carrito:fin_compra')
        
    except ValueError:
        # Marcar la transacción para rollback si ocurre un error validado (ej. stock insuficiente)
        try:
            transaction.set_rollback(True)
        except Exception:
            pass
        return redirect('carrito:carrito')
    

def compra_finalizada(request):
    """Muestra la página de confirmación después de una compra exitosa."""
    correo_pedido = request.session.pop('ultimo_correo_pedido', '')
    # Opcional: Recuperar el ID de pedido de la sesión/URL si lo estás manejando
    # y borrar la cesta de compra (si no se hizo en procesar_pago)
    opciones_filtro = obtener_opciones_filtro()

    contexto = {
        'mensaje_final': '¡Gracias por tu compra! Tu pedido ha sido procesado con éxito.',
        # Puedes añadir más información del pedido si la pasaste
        'correo': correo_pedido,
        'opciones_filtro': opciones_filtro, 
        
        # Estos valores se deben pasar vacíos para que el filtro no aparezca seleccionado por defecto en home
        'precio_seleccionado': '',
        'fabricante_seleccionado': '',
        'seccion_filtro_seleccionada': '',
    }
    return render(request, 'compra_finalizada.html', contexto)