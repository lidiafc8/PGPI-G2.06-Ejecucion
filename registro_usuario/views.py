from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate 
from .forms import RegistroUsuarioForm 

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST) 
        if form.is_valid():
            user = form.save() 
            
            email_a_autenticar = form.cleaned_data.get('corre_electronico')
            password = form.cleaned_data.get('password2') 
            
            authenticated_user = authenticate(
                request,
                username=email_a_autenticar, 
                password=password,
                backend='inicio_sesion.backends.ClienteBackend'
            )

            if authenticated_user is not None:
                login(request, authenticated_user) 
                
                return redirect('home') 

    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registro.html', {'form': form})