from django.shortcuts import render, redirect
from home.models import EstadoPedido, Pedido, UsuarioCliente
from decimal import Decimal # Importa Decimal para manejar dinero

def gestion_ventas(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    
    cliente_id = request.GET.get('cliente')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Clientes REGISTRADOS para el selector
    clientes_para_filtro = UsuarioCliente.objects.select_related('usuario').order_by('usuario__nombre')

    # Pedidos entregados
    pedidos_query = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO)

    # --- FILTRO POR CLIENTE ---
    if cliente_id:
        if cliente_id == "anonimo":
            pedidos_query = pedidos_query.filter(usuario_cliente__isnull=True)
        else:
            pedidos_query = pedidos_query.filter(usuario_cliente__id=cliente_id)

    # --- FILTRO POR FECHAS ---
    if fecha_inicio:
        pedidos_query = pedidos_query.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        pedidos_query = pedidos_query.filter(fecha_creacion__date__lte=fecha_fin)
        
    pedidos_filtrados_qs = pedidos_query.select_related('usuario_cliente__usuario').order_by('-fecha_creacion')

    pedidos_lista = list(pedidos_filtrados_qs)

    # --- Totales ---
    total_ganancias = sum((p.total_importe for p in pedidos_lista), Decimal('0.00'))
    total_ventas = len(pedidos_lista)

    # Evitar error si cliente_id == "anonimo"
    if cliente_id and cliente_id != "anonimo":
        try:
            cliente_seleccionado = int(cliente_id)
        except:
            cliente_seleccionado = None
    else:
        cliente_seleccionado = cliente_id  # "anonimo" o None

    # Contexto
    context = {
        'ventas': pedidos_lista,
        'clientes': clientes_para_filtro,
        'total_ganancias': total_ganancias,
        'total_ventas': total_ventas,

        'cliente_seleccionado': cliente_seleccionado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'ventas_admin/gestion_ventas.html', context)
