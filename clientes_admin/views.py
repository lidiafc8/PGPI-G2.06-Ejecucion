from django.shortcuts import render, redirect, get_object_or_404
from home.models import UsuarioCliente, Usuario
from django.http import HttpResponseNotAllowed

def gestion_clientes(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')

    if request.method == 'GET':

        clientes = UsuarioCliente.objects.select_related('usuario').order_by('usuario__nombre')

        context = {
            'clientes': clientes
        }
        return render(request, 'clientes_admin/gestion_clientes.html', context)
    else:
        return HttpResponseNotAllowed(['GET'])

def cliente_eliminar_confirmar(request, cliente_id):

    cliente = get_object_or_404(UsuarioCliente, id=cliente_id)

    if request.method == 'POST':
        try:
            usuario_a_eliminar = get_object_or_404(Usuario, usuariocliente__id=cliente_id)
            usuario_a_eliminar.delete()
            return redirect('clientes_admin_index')

        except Usuario.DoesNotExist:
            pass

        return redirect('clientes_admin_index')

    context = {
        'cliente': cliente
    }

    return render(request, 'clientes_admin/confirmar_eliminar.html', context)
