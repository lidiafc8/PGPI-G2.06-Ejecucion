from django.shortcuts import render, redirect
from home.models import EstadoPedido, Pedido, UsuarioCliente
from decimal import Decimal # Importa Decimal para manejar dinero

def gestion_ventas(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    
    cliente_id = request.GET.get('cliente')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    clientes_para_filtro = UsuarioCliente.objects.select_related('usuario').order_by('usuario__nombre')

    pedidos_query = Pedido.objects.filter(estado=EstadoPedido.ENTREGADO)

    if cliente_id:
        pedidos_query = pedidos_query.filter(usuario_cliente__id=cliente_id)
    if fecha_inicio:
        pedidos_query = pedidos_query.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        pedidos_query = pedidos_query.filter(fecha_creacion__date__lte=fecha_fin)
        
    pedidos_filtrados_qs = pedidos_query.select_related('usuario_cliente__usuario').order_by('-fecha_creacion')


    pedidos_lista = list(pedidos_filtrados_qs)
    
    total_ganancias = Decimal('0.00') 
    
    for pedido in pedidos_lista:
        total_ganancias += pedido.total_importe
        
    total_ventas = len(pedidos_lista)
    
    # --- Contexto para el Template ---
    context = {
        'ventas': pedidos_lista, 
        'clientes': clientes_para_filtro,
        'total_ganancias': total_ganancias,
        'total_ventas': total_ventas,
        
        'cliente_seleccionado': int(cliente_id) if cliente_id else None,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'ventas_admin/gestion_ventas.html', context)