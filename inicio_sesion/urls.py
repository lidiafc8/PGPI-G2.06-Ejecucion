from django.urls import path
from django.contrib.auth import views as auth_views
from .forms import ClienteAuthenticationForm 

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html', 
        authentication_form=ClienteAuthenticationForm,
        next_page='/'
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        next_page='/' 
    ), name='logout'),
]