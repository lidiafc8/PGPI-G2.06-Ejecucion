# perfil/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UsuarioEditForm, PerfilClienteEditForm 
from home.models import UsuarioCliente 

@login_required
def mi_perfil(request):
    usuario_instancia = request.user
    
    perfil_cliente_instancia, creado = UsuarioCliente.objects.get_or_create(usuario=usuario_instancia)

    if request.method == 'POST':
        user_form = UsuarioEditForm(request.POST, instance=usuario_instancia)
        perfil_form = PerfilClienteEditForm(request.POST, instance=perfil_cliente_instancia)
        
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            # Opcional: Mostrar un mensaje de éxito
            # messages.success(request, 'Tu perfil ha sido actualizado.')
            return redirect('perfil:mi_perfil') # Redirigir para evitar reenvío de formulario
            
    else:
        # Si es GET (al cargar la página), inicializa los formularios SOLO con las instancias
        user_form = UsuarioEditForm(instance=usuario_instancia)
        perfil_form = PerfilClienteEditForm(instance=perfil_cliente_instancia)

    contexto = {
        'user_form': user_form,
        'perfil_form': perfil_form,
    }
    
    return render(request, 'mi_perfil.html', contexto)