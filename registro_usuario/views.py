# registro_usuario/views.py

from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm # Asegúrate que la importación es correcta
from django.contrib.auth import login # Necesario si quieres loguear al usuario inmediatamente

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            # Aquí es donde llama a tu método save() personalizado
            cliente = form.save() 
            
            # Opcional: Iniciar sesión inmediatamente después del registro
            # login(request, cliente.usuario) 
            
            # Redirigir al login para que inicie sesión
            return redirect('inicio_sesion:login') 
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})