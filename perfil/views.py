# perfil/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse_lazy # Importar para usar con redirect, aunque 'perfil:admin_perfil' ya funciona

# Asegúrate de que estas importaciones son correctas
from home.models import UsuarioCliente 
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
        # Redirige al administrador a su perfil específico
        return redirect('perfil:admin_perfil')
        
    perfil_cliente_instancia, creado = UsuarioCliente.objects.get_or_create(usuario=usuario_instancia)
    
    # Manejo de POST (Guardar cambios del Cliente)
    if request.method == 'POST':
        # 🟢 3. Inicializar formularios con la instancia correcta para MODIFICAR
        user_form = UsuarioForm(request.POST, instance=usuario_instancia)
        perfil_form = PerfilClienteForm(request.POST, instance=perfil_cliente_instancia)

        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, "Perfil de Cliente actualizado correctamente.")
            # Redirige a la misma URL (patrón Post-Redirect-Get)
            return redirect('perfil:mi_perfil') 
        else:
            messages.error(request, "Error al actualizar el perfil. Revisa los datos.")
    else:
        # Manejo de GET (Mostrar formularios del Cliente)
        # Inicializar formularios con la instancia para MOSTRAR datos actuales
        user_form = UsuarioForm(instance=usuario_instancia)
        perfil_form = PerfilClienteForm(instance=perfil_cliente_instancia)
    
    contexto_cliente = {
        'user_form': user_form,
        'perfil_form': perfil_form, 
        'es_cliente': True,
    }
    
    return render(request, 'mi_perfil.html', contexto_cliente)

@login_required
def admin_perfil(request):
    """
    Muestra y maneja la edición del perfil para Administradores.
    """
    usuario_instancia = request.user
    
    # Manejo de POST (Guardar cambios del Admin)
    if request.method == 'POST':
        # Inicializar el formulario con la instancia de request.user
        user_form = UsuarioAdminForm(request.POST, instance=usuario_instancia)
        
        if user_form.is_valid():
            user_form.save()
            messages.success(request, "Perfil de Administrador actualizado correctamente.")
            
            # Redirige al panel principal del administrador tras guardar
            return redirect('adminpanel:adminpanel_index') 
        else:
            messages.error(request, "Error al actualizar el perfil de Administrador.")
    else:
        # Manejo de GET (Mostrar formulario del Admin)
        user_form = UsuarioAdminForm(instance=usuario_instancia)
    
    contexto_admin = {
        'user_form': user_form,
        'es_admin': True,
    }
    
    # Renderiza la plantilla SIMPLE para el Administrador
    return render(request, 'admin_perfil.html', contexto_admin)