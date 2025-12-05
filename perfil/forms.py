from django import forms
from django.contrib.auth import get_user_model
import re

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
    direccion_calle = forms.CharField(
        max_length=255,
        required=False,
        label="Calle y Número",
        widget=forms.TextInput(attrs={
            'placeholder': 'Calle, número, piso, etc.',
            'class': 'w-full outline-none border-none bg-transparent flex-1',
        })
    )
    
    direccion_cp = forms.CharField(
        max_length=10,
        required=False,
        label="Código Postal",
        widget=forms.TextInput(attrs={
            'placeholder': 'Código Postal',
            'class': 'w-full outline-none border-none bg-transparent flex-1',
        })
    )
    
    direccion_ciudad = forms.CharField(
        max_length=100,
        required=False,
        label="Ciudad",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ciudad',
            'class': 'w-full outline-none border-none bg-transparent flex-1',
        })
    )
    
    direccion_pais = forms.CharField(
        max_length=100,
        required=False,
        label="País",
        widget=forms.TextInput(attrs={
            'placeholder': 'País',
            'class': 'w-full outline-none border-none bg-transparent flex-1',
        })
    )


    class Meta:
        model = UsuarioCliente
        fields = ['telefono', 'tipo_pago', 'tipo_envio', 'direccion_envio'] 

        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'TELÉFONO', 'class': 'w-full outline-none'}),
            'tipo_pago': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
            'tipo_envio': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
            'direccion_envio': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            full_address = self.instance.direccion_envio
            parts_raw = [p.strip() for p in re.split(r',\s*', full_address)]
            
            parts = (parts_raw + ['', '', '', ''])[:4]
            self.initial['direccion_calle'] = parts[0]
            self.initial['direccion_cp'] = parts[1]
            self.initial['direccion_ciudad'] = parts[2]
            self.initial['direccion_pais'] = parts[3]
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        address_parts = [
            self.cleaned_data.get('direccion_calle'),
            self.cleaned_data.get('direccion_cp'),
            self.cleaned_data.get('direccion_ciudad'),
            self.cleaned_data.get('direccion_pais'),
        ]
        combined_address = ", ".join(filter(None, address_parts))
        instance.direccion_envio = combined_address

        if commit:
            instance.save()
        return instance
