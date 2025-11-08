from django import forms
from home.models import Usuario, UsuarioCliente 

class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'corre_electronico') 

class PerfilClienteEditForm(forms.ModelForm):
    class Meta:
        model = UsuarioCliente
        fields = ('tipo_pago', 'telefono', 'direccion_envio', 'tipo_envio')
        
    # Puedes añadir un constructor para personalizar el campo 'direccion_envio'
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['direccion_envio'].widget.attrs.update({'placeholder': 'Dirección completa'})