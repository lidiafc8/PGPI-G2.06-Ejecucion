# registro_usuario/views.py (Código corregido)

from django.shortcuts import render, redirect
from django.contrib.auth import login 
from .forms import RegistroUsuarioForm 

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            
            # 🌟 CORRECCIÓN CLAVE: Especificar el backend
            login(request, user, backend='inicio_sesion.backends.ClienteBackend') 
            
            # Redirige al usuario
            return redirect('home') 
        # Si el formulario no es válido, asegúrate de que se renderiza el template.
        # Recuerda la corrección de la ruta del template que vimos antes.
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})