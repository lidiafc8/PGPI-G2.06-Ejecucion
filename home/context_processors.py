from .models import CestaCompra

def productos_en_cesta(request):
    total_items = 0

    if request.user.is_authenticated:
        try:
            cesta = CestaCompra.objects.get(usuario_cliente__usuario=request.user)
        except CestaCompra.DoesNotExist:
            cesta = None
    else:
        session_id = request.session.get("cesta_id")
        cesta = CestaCompra.objects.filter(session_id=session_id).first() if session_id else None

    if cesta:
        total_items = sum(item.cantidad for item in cesta.items.all())

    return {'total_items_cesta': total_items}
