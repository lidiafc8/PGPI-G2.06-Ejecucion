from django.shortcuts import render, redirect
from django.contrib.auth import login 
from django.contrib.auth.decorators import login_required 
from django.urls import reverse_lazy 

from .forms import ClienteAuthenticationForm 

def login_view(request):

    if request.user.is_authenticated: 
        return redirect('adminpanel:adminpanel_index') 

    if request.method == 'POST':
        form = ClienteAuthenticationForm(request=request, data=request.POST) 

        if form.is_valid(): 
            user = form.get_user()
            login(request, user) 

            return redirect('inicio_sesion:post_login_redirect') 

    else:
        form = ClienteAuthenticationForm(request=request)

    return render(request, 'login.html', {'form': form})

@login_required
def post_login_redirect(request):
    """
    Decide la página de inicio en función del rol del usuario.
    """
    user = request.user

    if user.is_superuser or (hasattr(user, 'es_administrador') and user.es_administrador):
        return redirect(reverse_lazy('adminpanel:adminpanel_index'))
    else:
        return redirect('/')