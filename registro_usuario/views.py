from django.shortcuts import render

from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm  

def registro(request):
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            user = form.save()
            return redirect('/') 

    else:
        form = RegistroUsuarioForm()

    return render(request, 'registro.html', {'form': form})