from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy
from home.models import UsuarioCliente, Pedido
from .forms import UsuarioForm, PerfilClienteForm, UsuarioAdminForm

Usuario = get_user_model()

@login_required
def mi_perfil(request):
    """
    Muestra y maneja la edición del perfil para usuarios normales (Clientes).
    """
    usuario_instancia = request.user

    if usuario_instancia.is_superuser or (hasattr(usuario_instancia, 'es_administrador') and usuario_instancia.es_administrador):
        messages.warning(request, "Eres Admin")
        return redirect('perfil:admin_perfil')

    perfil_cliente_instancia, creado = UsuarioCliente.objects.get_or_create(usuario=usuario_instancia)

    if request.method == 'POST':
        user_form = UsuarioForm(request.POST, instance=usuario_instancia)
        perfil_form = PerfilClienteForm(request.POST, instance=perfil_cliente_instancia)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil de Cliente actualizado correctamente.")
            return redirect('perfil:mi_perfil')
        else:
            messages.error(request, "Error al actualizar el perfil. Revisa los datos.")
    else:
        user_form = UsuarioForm(instance=usuario_instancia)
        perfil_form = PerfilClienteForm(instance=perfil_cliente_instancia)

    contexto_cliente = {
        'user_form': user_form,
        'perfil_form': perfil_form,
        'es_cliente': True,
    }

    return render(request, 'mi_perfil.html', contexto_cliente)

@login_required
def lista_pedidos_cliente(request):
    """Muestra una lista de todos los pedidos realizados por el cliente."""
    try:
        usuario_cliente = request.user.usuariocliente
    except UsuarioCliente.DoesNotExist:
        messages.error(request, "Tu perfil no está registrado como cliente.")
        return redirect('perfil:mi_perfil')
    pedidos = Pedido.objects.filter(usuario_cliente=usuario_cliente).order_by('fecha_creacion')

    context = {
        'pedidos': pedidos,
    }
    return render(request, 'lista_pedidos_cliente.html', context)

@login_required
def ver_ticket_pedido(request, pedido_id):
    """Muestra los detalles completos de un pedido específico (el ticket/factura)."""
    try:
        usuario_cliente = request.user.usuariocliente
    except UsuarioCliente.DoesNotExist:
        messages.error(request, "Acceso denegado: debes ser un cliente.")
        return redirect('perfil:mi_perfil')
    pedido = get_object_or_404(Pedido, id=pedido_id, usuario_cliente=usuario_cliente)
    items_pedido = pedido.items.all()
    context = {
        'pedido': pedido,
        'items': items_pedido,
    }
    return render(request, 'ticket_pedido.html', context)

@login_required
def admin_perfil(request):
    """
    Muestra y maneja la edición del perfil para Administradores.
    """
    usuario_instancia = request.user

    if request.method == 'POST':
        user_form = UsuarioAdminForm(request.POST, instance=usuario_instancia)

        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Perfil de Administrador actualizado correctamente.")

            return redirect('adminpanel:adminpanel_index')
        else:
            messages.error(request, "Error al actualizar el perfil de Administrador.")
    else:
        user_form = UsuarioAdminForm(instance=usuario_instancia)

    contexto_admin = {
        'user_form': user_form,
        'es_admin': True,
    }

    return render(request, 'admin_perfil.html', contexto_admin)
