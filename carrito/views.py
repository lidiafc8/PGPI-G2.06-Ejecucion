from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from home.models import Producto 
from decimal import Decimal 
from django.contrib import messages
from home.models import (
    Producto, CestaCompra, UsuarioCliente, ItemCestaCompra,
    Pedido, ItemPedido, TipoPago, TipoEnvio, EstadoPedido, Tarjeta
)

import uuid 
from django.db import transaction # Importar para asegurar la integridad de los datos




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
def update_cart(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cesta = obtener_cesta_actual(request) 
    item = ItemCestaCompra.objects.get(cesta_compra=cesta, producto_id=producto_id)
    
    action = request.POST.get('action') 

    if action == 'add':
        if item.cantidad +1 > producto.stock:
            messages.error(request, f"Lo sentimos, solo quedan {producto.stock} unidades de {producto.nombre}.")
        else:
            item.cantidad += 1
            item.save()
    elif action == 'remove':
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
        elif item.cantidad == 1:

            item.delete()
    
    return redirect('carrito:carrito')

@require_POST 
def remove_from_cart(request, producto_id):
    cesta = obtener_cesta_actual(request)
    if not cesta:
        return redirect('carrito:carrito') 

    try:

        item = ItemCestaCompra.objects.get(cesta_compra=cesta, producto_id=producto_id)
        item.delete()
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

    cesta= None

    if request.user.is_authenticated:
        # Usuario registrado
        usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
        cesta, creada = CestaCompra.objects.get_or_create(usuario_cliente=usuario_cliente)
    else:
        # Usuario anónimo
        session_id = request.session.get("cesta_id")
        if session_id:
            cesta = CestaCompra.objects.filter(session_id=session_id).first()
        else:
            cesta = None

    if cesta:
        items = cesta.items.all()
        for item in items:
            if item.producto.stock > 0:
                # item es un objeto ItemCestaCompra
                precio_linea = item.producto.precio * item.cantidad
                subtotal += precio_linea
                
            articulos_para_plantilla.append({
                    'id': item.producto.id, 
                    'nombre': item.producto.nombre,
                    'imagen_url': item.producto.imagen.url,
                    'precio_unidad': item.producto.precio,
                    'cantidad': item.cantidad,
                    'precio_total': precio_linea,
                    'stock': item.producto.stock,
                })
        total = subtotal 

    context = {
    
    'articulos': articulos_para_plantilla, 
    'subtotal': f"{subtotal:.2f}",
    'total': f"{total:.2f}", 
    }

    return render(request, "carrito.html", context)

def checkout(request):
    """
    Vista que muestra la página de pago (GET).
    Asegura que los totales y los artículos de la cesta se pasen a la plantilla.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
         messages.error(request, "Tu carrito está vacío. Añade productos antes de pagar.")
         return redirect('carrito:carrito')
         
    # Cálculos necesarios para mostrar los valores iniciales en la plantilla
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        subtotal += item.producto.precio * item.cantidad
    coste_envio= Decimal('0.00')
    coste_envio = 0
    if(subtotal < 50):
        coste_envio =  5
  
    total_inicial=subtotal+coste_envio
    tarjetas_guardadas = None
    tiene_tarjeta_guardada = False
    tarjetas_para_contexto = []
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
            
        except UsuarioCliente.DoesNotExist:
            pass

    # 2. Actualizar el contexto con la nueva lista de tarjetas
    context = {
        'articulos': cesta.items.all(),
        'subtotal': f"{subtotal:.2f}",
        'coste_envio': coste_envio,
        'total': f"{total_inicial:.2f}",
        
        # Nuevas variables de tarjeta:
        'tarjetas_para_contexto': tarjetas_para_contexto, # La lista de tarjetas procesadas
        'tiene_tarjeta_guardada': bool(tarjetas_para_contexto), # True si la lista no está vacía
    }
    
    return render(request, "pago.html", context)

@require_POST
@transaction.atomic 
def procesar_pago(request):
    """
    Procesa la solicitud POST del formulario de pago:
    1. Valida y calcula costes.
    2. Crea el Pedido e ItemPedido.
    3. Reduce el stock.
    4. Vacía la cesta.
    """
    cesta = obtener_cesta_actual(request)
    
    if not cesta or not cesta.items.exists():
        messages.error(request, "El carrito está vacío. No se puede procesar el pago.")
        return redirect('carrito:carrito')
        

    # 0. Obtener datos del formulario
    entrega_value = request.POST.get('shipping_option') # 'standard' o 'express'
    payment_method_value = request.POST.get('payment_method') # 'gateway' o 'cash'
    email = request.POST.get('contact_email') # 'gateway' o 'cash'
    telefon = request.POST.get('contact_phone') # 'gateway' o 'cash'
    calle = request.POST.get('address_street') # 'gateway' o 'cash'
    ciudad = request.POST.get('address_city') # 'gateway' o 'cash'
    cpi = request.POST.get('address_zip') # 'gateway' o 'cash'
    pais = request.POST.get('address_country') # 'gateway' o 'cash'

    # Datos de Tarjeta (solo si el método es 'gateway')
    card_number = request.POST.get('card_number')
    expiry_date = request.POST.get('expiry_date') # MM/AA
    card_cvv = request.POST.get('cvv') #  CV
    # Flag para guardar tarjeta (solo presente si el usuario está autenticado)
    save_card_flag = request.POST.get('save_card') == 'on'

    # 1. Obtener direccion
    direccion = f"{calle}, {cpi} {ciudad}, {pais}"


    # 2. Calcular costes
    subtotal = Decimal('0.00')
    for item in cesta.items.all():
        subtotal += item.producto.precio * item.cantidad

    coste_entrega = Decimal('0.00')
    coste_entrega = 0
    if(subtotal < 50):
        coste_entrega =  5
  

    if payment_method_value == 'cash':
        metodo_pago = TipoPago.CONTRAREEMBOLSO
    else: 
        metodo_pago = TipoPago.PASARELA_PAGO
    
    if entrega_value == 'standard':
        metodo_envio = TipoEnvio.DOMICILIO
    else: 
        metodo_envio = TipoEnvio.RECOGIDA_TIENDA

    total_importe = subtotal + coste_entrega
    
    if metodo_pago == TipoPago.PASARELA_PAGO:
        pago = True
    else:
        pago = False

    usuario_cliente = None
    if request.user.is_authenticated:
        try:
            # Asume que tu modelo UsuarioCliente tiene una FK llamada 'usuario' al User de Django
            usuario_cliente = UsuarioCliente.objects.get(usuario=request.user)
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
    # Dirección y datos de contacto tomados del UsuarioCliente
    try:
        # 3. Crear el Pedido (Registro principal)
        pedido = Pedido.objects.create(
            usuario_cliente=usuario_cliente, # Instancia o None
            estado=EstadoPedido.PEDIDO, 
            subtotal_importe=subtotal,
            coste_entrega=coste_entrega, 
            total_importe=total_importe,
            metodo_pago=metodo_pago,
            tipo_envio=metodo_envio, 
            direccion_envio=direccion,
            correo_electronico=email,
            telefono=telefon,
            pago=pago,
        )

        # 4. Crear ItemPedido y Actualizar Stock
        for item_cesta in cesta.items.select_related('producto'):
            producto = item_cesta.producto
            
            # ⚠️ Verificación de Stock y Reducción
            if item_cesta.cantidad > producto.stock:
                messages.error(request, f"Lo sentimos, el stock de {producto.nombre} ha cambiado. Solo quedan {producto.stock} unidades.")
                # Si el stock falla, lanzamos la excepción. Esta acción fuerza el rollback de @transaction.atomic 
                # y es capturada por el bloque 'except ValueError' para redirigir al carrito.
                raise ValueError("Stock insuficiente.") 

            # Crear ItemPedido (Guarda el precio del momento)
            ItemPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item_cesta.cantidad,
                precio_unitario=item_cesta.producto.precio,
            )
            
            # Reducir Stock
            producto.stock -= item_cesta.cantidad
            producto.save()


        # 5. Vaciar Cesta (Solo se ejecuta si el loop de stock termina con éxito)
        cesta.items.all().delete()
        
        messages.success(request, f"🛒 ¡Pedido #{pedido.id} realizado con éxito! Total a pagar: {total_importe:.2f} €")
        
    except ValueError:
        # Se captura el ValueError lanzado durante la verificación de stock.
        # La transacción ya fue revertida por @transaction.atomic.
        # Ahora redirigimos al carrito sin un error 500.
        return redirect('carrito:carrito') 

    # 5. Vaciar Cesta
    cesta.items.all().delete()
    
    messages.success(request, f"🛒 ¡Pedido #{pedido.id} realizado con éxito! ")
    return redirect('home') # O redirigir a una página de confirmación real