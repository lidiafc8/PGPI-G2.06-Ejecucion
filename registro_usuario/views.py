from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate 
from django.contrib import messages 
from .forms import RegistroUsuarioForm 
from home.models import Usuario 

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST) 
        if form.is_valid():
            
            cliente = form.save() 
            user = cliente.usuario 

            email_a_autenticar = form.cleaned_data.get('corre_electronico')
            password = form.cleaned_data.get('password') 
            
            authenticated_user = authenticate(
                request,
                username=email_a_autenticar, 
                password=password,
                backend='inicio_sesion.backends.ClienteBackend' 
            )

            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, '¡Tu cuenta se ha creado con éxito! Has iniciado sesión automáticamente.')
                return redirect('home')
            else:
                messages.warning(request, 'Cuenta creada, pero no se pudo iniciar sesión automáticamente. Inténtalo manualmente.')
                return redirect('inicio_sesion:login')
        
        else:
             pass

    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})