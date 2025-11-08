from django.contrib.auth.forms import AuthenticationForm
from home.models import Usuario, UsuarioCliente 
from django import forms
from django.core.exceptions import ValidationError 

class ClienteAuthenticationForm(AuthenticationForm):
    """
    Formulario personalizado para la autenticación del Cliente. 
    Utiliza 'corre_electronico' como campo de identificación principal.
    """
    
    username = forms.CharField(
        label="Correo Electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autofocus': True, 
            'placeholder': 'CORREO ELECTRÓNICO' 
        }) 
    )
    
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'CONTRASEÑA'
        })
    )
    
    def clean(self):
        
        corre_electronico = self.cleaned_data.get('username') 
        password = self.cleaned_data.get('password')
        
        if corre_electronico and password:
            try:
                usuario = Usuario.objects.get(corre_electronico=corre_electronico)
                
                if not usuario.check_password(password):
                    raise self.get_invalid_login_error() 
            
            except Usuario.DoesNotExist:
                raise self.get_invalid_login_error()
            
            if not UsuarioCliente.objects.filter(usuario=usuario).exists():
                raise ValidationError(
                    'Solo los usuarios con perfil de cliente pueden acceder.',
                    code='inactive' 
                )
            
            self.user_cache = usuario

        return self.cleaned_data
    
    def get_invalid_login_error(self):
        """
        Un método auxiliar para generar el error genérico de login.
        """
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )
