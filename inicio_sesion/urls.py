from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from .forms import ClienteAuthenticationForm # Asegúrate de que esta forma funciona correctamente
from . import views

def custom_logout_view(request):
    """
    Función para desloguear al usuario y redirigir a la página principal.
    """
    logout(request)
    return redirect('/')

def cambio_rol(request):
    """
    Redirige al usuario después del login basándose en su rol.
    Asume que tienes un campo o método en el modelo User para verificar si es administrador.
    """
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('adminpanel:adminpanel_index') 
    elif request.user.is_authenticated:
        return redirect('/') 
    else:
        return redirect('inicio_sesion:login')


app_name = 'inicio_sesion'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html', 
        authentication_form=ClienteAuthenticationForm,
    ), name='login'),

    path('logout/', custom_logout_view, name='logout'), 

    # URL para la redirección condicional
    path('cambio_rol/', cambio_rol, name='cambio_rol'),
]