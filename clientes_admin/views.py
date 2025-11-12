from django.shortcuts import render, redirect, get_object_or_404
from home.models import UsuarioCliente, Usuario  # Asegúrate de importar
from django.http import HttpResponseNotAllowed

# ESTA ES LA VISTA QUE ENVÍA LOS DATOS A TU PLANTILLA
def gestion_clientes(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    
    if request.method == 'GET':
        # Esta línea es la que busca los clientes
        clientes = UsuarioCliente.objects.select_related('usuario').order_by('usuario__nombre')
        
        # Y esta línea se los pasa a la plantilla
        context = {
            'clientes': clientes
        }
        return render(request, 'clientes_admin/gestion_clientes.html', context)
    else:
        return HttpResponseNotAllowed(['GET'])


# Esta es la OTRA vista, la de confirmar eliminación.
# Esta NO se encarga de mostrar la lista.
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
    # Asegúrate de que esta renderiza la plantilla de CONFIRMACIÓN
    return render(request, 'clientes_admin/confirmar_eliminar.html', context)