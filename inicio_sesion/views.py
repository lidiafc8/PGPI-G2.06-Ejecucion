# inicio_sesion/views.py (Revisión Completa)

from django.shortcuts import render, redirect
from django.contrib.auth import login 
from django.contrib.auth.decorators import login_required 
from django.urls import reverse_lazy 

# Asumiendo que esta es la ubicación correcta de tu formulario de autenticación
from .forms import ClienteAuthenticationForm 

def login_view(request):
    
    # Si el usuario ya está autenticado, redirigirlo a la vista que distribuye roles
    if request.user.is_authenticated: 
        # 🟢 CORRECCIÓN 1: Si ya está autenticado, enviarlo directamente al distribuidor
        # Esto previene que un usuario logueado tenga que pasar por el login.
        return redirect('inicio_sesion:post_login_redirect') 
        
    if request.method == 'POST':
        # Nota: La forma correcta de inicializar AuthenticationForm es pasando request
        form = ClienteAuthenticationForm(request=request, data=request.POST) 
        
        if form.is_valid(): 
            user = form.get_user()
            # 🚨 El login se realiza correctamente aquí, por lo que la sesión se establece.
            login(request, user) 
            
            return redirect('inicio_sesion:post_login_redirect') 
        
        # 💡 MEJORA: Mostrar errores del formulario
        # Si el formulario no es válido (credenciales incorrectas), messages.error o pasar el error al template.
        
    else:
        form = ClienteAuthenticationForm(request=request)

    return render(request, 'login.html', {'form': form})

# ----------------------------------------------------------------------------------

# Esta vista ya estaba bien definida para distribuir el tráfico, solo necesitaba ser llamada
@login_required
def post_login_redirect(request):
    """
    Decide la página de inicio en función del rol del usuario.
    """
    user = request.user
    
    if user.is_superuser or (hasattr(user, 'es_administrador') and user.es_administrador):
        return redirect(reverse_lazy('perfil:admin_perfil'))
    else:
        return redirect(reverse_lazy('perfil:mi_perfil'))