from django.shortcuts import render, redirect, get_object_or_404
from home.models import Pedido 
from django.views.decorators.http import require_POST
from .forms import PedidoEstadoForm 
from django.contrib import messages

def lista_pedidos(request):
    """
    Vista principal para el administrador. Muestra una lista de todos los pedidos.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    pedidos = Pedido.objects.all().order_by('fecha_creacion') 
    context = {'pedidos': pedidos}
    return render(request, 'lista_pedidos.html', context)


def detalle_pedido(request, pk):
    """
    Muestra los detalles de un pedido específico y permite actualizar su estado.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    
    # 1. Obtener el pedido y guardar el estado de pago ANTES de cualquier cambio
    pedido = get_object_or_404(Pedido, pk=pk)
    pago_previo = pedido.pago
    
    if request.method == 'POST':
        form = PedidoEstadoForm(request.POST, instance=pedido)
        
        if form.is_valid():
            # Guarda el pedido con el nuevo estado
            pedido_actualizado = form.save(commit=False)
            nuevo_estado = pedido_actualizado.estado

            # 2. Lógica para Pago Contra Reembolso
            # Si el nuevo estado es 'ENTREGADO' y el pago aún no se ha registrado, se marca como pagado.
            if nuevo_estado == 'ENTREGADO' and not pago_previo:
                pedido_actualizado.pago = True
                messages.success(request, "✅ El pedido ha sido marcado como **ENTREGADO** y, dado que no estaba pagado previamente (contra reembolso), se ha actualizado su estado de pago a **PAGADO**.")
            
            # Guarda el modelo (con o sin el cambio de pago)
            pedido_actualizado.save()

            if nuevo_estado != 'ENTREGADO' or pago_previo:
                 messages.success(request, f"El estado del pedido #{pk} se ha actualizado correctamente a **{pedido.estado}**.")
            
            return redirect('detalle_pedido', pk=pk)
        
        else:
            messages.error(request, "Error al actualizar el estado del pedido. Revisa los errores del formulario.")
    else:
        form = PedidoEstadoForm(instance=pedido) 

    context = {
        'pedido': pedido,
        'form': form, 
    }
    return render(request, 'detalle_pedido.html', context)


def admin_dashboard(request):
    """
    Mantiene la vista del panel de administración (index).
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    return render(request, 'adminpanel/index.html')