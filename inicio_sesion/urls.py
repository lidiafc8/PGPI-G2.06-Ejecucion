from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .forms import ClienteAuthenticationForm 
from django.contrib.auth import logout 
from django.shortcuts import redirect 
from . import views

def custom_logout_view(request):
    logout(request)
    return redirect('/') 

app_name = 'inicio_sesion'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html', 
        authentication_form=ClienteAuthenticationForm,
    ), name='login'),
    
    path('logout/', custom_logout_view, name='logout'), 
]