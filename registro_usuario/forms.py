from django import forms
from home.models import Usuario, UsuarioCliente 

class RegistroUsuarioForm(forms.Form):
    
    nombre = forms.CharField(max_length=100, label="Nombre")
    apellidos = forms.CharField(max_length=200, label="Apellidos")
    corre_electronico = forms.EmailField(max_length=200, label="Correo Electrónico")
    
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")
    
    telefono = forms.CharField(max_length=15, required=False, label="Teléfono (Opcional)") 
    
    direccion_envio = forms.CharField(max_length=255, label="Dirección de Envío")
    
    
    def clean_password2(self):
        """Asegura que las dos contraseñas coincidan."""
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('¡Las contraseñas no coinciden!')
        return cd['password2']
    
    def clean_corre_electronico(self):
        """Asegura que el email no esté ya registrado en la tabla Usuario."""
        email = self.cleaned_data['corre_electronico']
        if Usuario.objects.filter(corre_electronico=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self):
        """Crea las dos instancias de modelo (Usuario y UsuarioCliente)."""
        cd = self.cleaned_data
        
        usuario = Usuario.objects.create(
            nombre=cd['nombre'],
            apellidos=cd['apellidos'],
            corre_electronico=cd['corre_electronico']
        )
        
        usuario.set_password(cd['password'])
        usuario.save()
        
        cliente = UsuarioCliente.objects.create(
            usuario=usuario, 
            telefono=cd.get('telefono'), 
            direccion_envio=cd['direccion_envio'],
        )
        
        return cliente 