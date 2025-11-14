from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
import uuid
from .models import Producto, UsuarioCliente, CestaCompra, ItemCestaCompra
from django.contrib import messages
from django.http import JsonResponse

# El parámetro 'categoria' contendrá el valor de la URL (ej: 'CORTASETOS_Y_MOTOSIERRAS')
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

    contexto = {
        'productos_destacados': productos_a_mostrar,
        'categoria_actual': categoria_valor,
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

    contexto = {
        'producto': producto,
        'productos_relacionados': productos_relacionados,
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

    contexto = {
        'query': query,
        'productos_destacados': productos_encontrados,
        'categoria_actual': f'Resultados para "{query}"' if query else 'Búsqueda',
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


def ver_cesta(request):
    """
    Muestra la cesta unificada para todos los usuarios.
    """
    items = []
    total = 0

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
        total = cesta.get_total_cesta()

    return render(request, "cesta.html", {"items": items, "total": total})