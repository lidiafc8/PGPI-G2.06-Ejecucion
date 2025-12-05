from django import forms
from django.contrib.auth import get_user_model

from home.models import UsuarioCliente, Usuario

Usuarios = get_user_model()

class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellidos', 'corre_electronico']

        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            'corre_electronico': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none'}),
        }

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'corre_electronico')

        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            'corre_electronico': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none'}),
        }

class PerfilClienteForm(forms.ModelForm):

    class Meta:
        model = UsuarioCliente
        fields = ['telefono', 'tipo_pago', 'tipo_envio', 'direccion_envio']

        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'TELÉFONO', 'class': 'w-full outline-none'}),

            'direccion_envio': forms.TextInput(attrs={
                'placeholder': 'Ej: Calle Principal, 123, 28001 Madrid, España',
                'class': 'w-full outline-none border-none bg-transparent flex-1',
            }),

            'tipo_pago': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
            'tipo_envio': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
        }

