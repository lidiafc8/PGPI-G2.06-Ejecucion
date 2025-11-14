from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from home.models import Producto 
from decimal import Decimal 
from django.contrib import messages

from home.models import CestaCompra, UsuarioCliente, ItemCestaCompra
import uuid 

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