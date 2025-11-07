from django.shortcuts import render

from home.models import EstadoPedido, Pedido, UsuarioCliente

# esto se usa cuando haya base de datos 
def gestion_ventas(request):
    pedidos = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO).order_by('-fecha_creacion')
    total_ganancias = sum(p.total for p in pedidos)
    total_ventas = pedidos.count

    return render(request, 'ventas_admin/gestion_ventas.html', {
        'ventas': pedidos,
        'total_ganancias': total_ganancias,
        'total_ventas': total_ventas,
    })
    
def ventas_por_cliente(request):
    clientes = UsuarioCliente.objects.select_related('usuario').order_by('usuario__nombre')
    
    cliente_id = request.GET.get('cliente')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    pedidos = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO)

    # Aplicamos filtros si existen
    if cliente_id:
        pedidos = pedidos.filter(cliente_id=cliente_id)
    if fecha_inicio:
        pedidos = pedidos.filter(fecha_creacion__gte=fecha_inicio)
    if fecha_fin:
        pedidos = pedidos.filter(fecha_creacion__lte=fecha_fin)

    # Ordenamos por fecha descendente
    pedidos = pedidos.order_by('-fecha_creacion')

    # Calculamos totales sobre los pedidos filtrados
    total_ganancias = sum(p.total for p in pedidos)
    total_ventas = pedidos.count()

    return render(request, 'ventas_admin/ventas_por_cliente.html', {
        'clientes': clientes,
        'pedidos': pedidos,
        'total_ganancias': total_ganancias,
        'total_ventas': total_ventas,
        'cliente_seleccionado': int(cliente_id) if cliente_id else None,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })