from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

class ClienteAuthenticationForm(AuthenticationForm):
    """
    Formulario personalizado para la autenticación. 
    Utiliza 'corre_electronico' como campo de identificación principal 
    y elimina la validación de rol para permitir el acceso a cualquier usuario autenticado.
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

        username_input = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_input and password:
            self.user_cache = authenticate(
                self.request,
                username=username_input,
                password=password
            )

            if self.user_cache is None:
                raise self.get_invalid_login_error()

            self.confirm_login_allowed(self.user_cache)

        return super().clean()

    def get_invalid_login_error(self):
        return ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )
