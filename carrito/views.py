from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from home.models import Producto 
from decimal import Decimal 

def carrito(request):
    
    carrito_sesion = request.session.get('carrito', {})
    print(carrito_sesion)
    # CORRECCIÓN 1: Asegurar que los IDs para la consulta sean enteros.
    # Las claves de la sesión son cadenas, y los IDs de la DB son enteros.
    try:
        producto_ids_int = [int(id_str) for id_str in carrito_sesion.keys()]
    except ValueError:
        producto_ids_int = [] # Si hay datos corruptos, evitamos fallar

    productos = Producto.objects.filter(id__in=producto_ids_int)
    
    subtotal = Decimal('0.00')
    gastos_envio = Decimal('0.00')
    articulos_para_plantilla = []
    
    for producto in productos:
        # Usamos str(producto.id) para buscar la cantidad en la sesión
        cantidad = int(carrito_sesion.get(str(producto.id), 0)) 
        
        if cantidad > 0:
            precio_linea = producto.precio * cantidad
            subtotal += precio_linea

            articulos_para_plantilla.append({
                # ¡CRUCIAL! Añadir el ID para que los botones de la plantilla funcionen
                'id': producto.id, 
                'nombre': producto.nombre,
                
                # CORRECCIÓN 2: Usar .url para obtener la ruta del archivo de imagen
                'imagen_url': producto.imagen.url if producto.imagen else '/static/img/placeholder.jpg',
                
                'precio_unidad': producto.precio,
                'cantidad': cantidad,
                'precio_total': precio_linea,
            })
    
    # ... (El resto del cálculo del total y gastos de envío es correcto)
    
    if subtotal < Decimal('150.00') and subtotal > Decimal('0.00'):
        gastos_envio = Decimal('19.95')
        
    total = subtotal + gastos_envio
    
    context = {
        'articulos': articulos_para_plantilla, 
        'subtotal': f"{subtotal:.2f}",
        'gastos_envio': f"{gastos_envio:.2f}",
        'total': f"{total:.2f}",
    }

    return render(request, 'carrito.html', context)

@require_POST 
def update_cart(request, item_id):
    """Añade o resta una unidad de un producto en el carrito."""
    try:
        # Intentamos obtener el producto (aunque solo necesitamos el ID para la sesión)
        # Esto sirve para comprobar que el producto existe.
        producto = get_object_or_404(Producto, id=item_id)
    except:
        return JsonResponse({'success': False, 'message': 'Producto no encontrado'}, status=404)

    action = request.GET.get('action') # Obtener la acción: 'add' o 'remove'
    carrito_sesion = request.session.get('carrito', {})
    item_id_str = str(item_id)

    if item_id_str in carrito_sesion:
        cantidad = int(carrito_sesion[item_id_str])

        if action == 'add':
            cantidad += 1
        elif action == 'remove' and cantidad > 1:
            cantidad -= 1
        elif action == 'remove' and cantidad == 1:
            # Si se pide eliminar y la cantidad es 1, lo eliminamos completamente
            del carrito_sesion[item_id_str]
            request.session.modified = True
            # Es mejor redirigir para recargar la vista después de una eliminación total
            return redirect('carrito') # Redirigir a la vista del carrito
        else:
            # Si la acción es 'remove' y la cantidad es 0 o no válida, no hacemos nada
            return redirect('carrito')


        carrito_sesion[item_id_str] = cantidad
        request.session.modified = True

        # **Opción 1:** Redirigir a la vista del carrito para que recargue los datos
        return redirect('carrito')

        # **Opción 2:** Si usas AJAX, devolver un JSON (más avanzado)
        # precio_linea = producto.precio * cantidad
        # return JsonResponse({
        #     'success': True,
        #     'new_quantity': cantidad,
        #     'new_total_price': f"{precio_linea:.2f}",
        # })

    return redirect('carrito') # Si el producto no estaba en el carrito

@require_POST 
def remove_from_cart(request, item_id):
    """Elimina completamente un producto del carrito."""
    carrito_sesion = request.session.get('carrito', {})
    item_id_str = str(item_id)

    if item_id_str in carrito_sesion:
        del carrito_sesion[item_id_str]
        request.session.modified = True

    return redirect('carrito')