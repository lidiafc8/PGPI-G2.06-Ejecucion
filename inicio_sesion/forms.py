# forms.py (Versión Corregida)

from django.contrib.auth.forms import AuthenticationForm
from home.models import Usuario, UsuarioCliente 
from django import forms
from django.core.exceptions import ValidationError 
from django.contrib.auth import authenticate # ¡IMPORTACIÓN NECESARIA!

class ClienteAuthenticationForm(AuthenticationForm):
    """
    Formulario personalizado para la autenticación del Cliente. 
    Utiliza 'corre_electronico' como campo de identificación principal.
    """
    
    # ... (Definición de username y password, que está correcta) ...

    # Sobrescribimos el campo username para que se muestre como Correo Electrónico
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
        
        # 1. Obtener los datos limpios (email y password)
        corre_electronico = self.cleaned_data.get('username') 
        password = self.cleaned_data.get('password')
        
        if corre_electronico and password:
            
            # 2. INTENTO DE AUTENTICACIÓN ESTÁNDAR DE DJANGO
            # Usamos authenticate, que buscará en el backend por email/password.
            # NOTA: Esto solo funciona si tu backend o modelo de usuario personalizado 
            # está configurado para usar el correo como USERNAME_FIELD.
            self.user_cache = authenticate(
                self.request, 
                username=corre_electronico, 
                password=password
            )

            # 3. Verificar si la autenticación falló
            if self.user_cache is None:
                # Lanza el error genérico de login (Usuario o Contraseña incorrectos)
                raise self.get_invalid_login_error()

            # 4. Verificar si el usuario está activo y permitir login (FUNCIÓN CRÍTICA)
            self.confirm_login_allowed(self.user_cache)
            
            # 5. VALIDACIÓN ADICIONAL (Verificar si tiene perfil de cliente)
            # Solo si el usuario fue autenticado exitosamente:
            if not UsuarioCliente.objects.filter(usuario=self.user_cache).exists():
                raise ValidationError(
                    'Solo los usuarios con perfil de cliente pueden acceder.',
                    code='inactive' 
                )
            
        # 6. Retorna los datos limpios
        return self.cleaned_data
    
    # Mantienes tu get_invalid_login_error
    def get_invalid_login_error(self):
        # ... (Tu código original)
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )