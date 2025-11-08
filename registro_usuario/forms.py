from django import forms
from home.models import Usuario, UsuarioCliente 
from home.models import TipoPago, TipoEnvio 
from django.core.validators import MinLengthValidator, RegexValidator

class RegistroUsuarioForm(forms.Form):
    
    nombre = forms.CharField(
        max_length=100, 
        label="Nombre",
        widget=forms.TextInput(attrs={'placeholder': 'NOMBRE'})
    )
    
    apellidos = forms.CharField(
        max_length=200, 
        label="Apellidos",
        widget=forms.TextInput(attrs={'placeholder': 'APELLIDOS'})
    )
    
    corre_electronico = forms.EmailField(
        max_length=200, 
        label="Correo Electrónico",
        error_messages={'invalid': '¡Vaya! Introduce una dirección de correo válida. Por ejemplo: nombre@dominio.com'},
        widget=forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'CONTRASEÑA'}),
        label="Contraseña"
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'CONFIRMAR CONTRASEÑA'}), 
        label="Confirmar contraseña"
    )
    
    telefono = forms.CharField(
        max_length=15, 
        min_length=9, 
        required=False, 
        label="Teléfono (Opcional)",
        validators=[
            RegexValidator(r'^\d+$', message="El teléfono solo debe contener números."),
            MinLengthValidator(9, message="El teléfono debe tener un mínimo de 9 dígitos.")
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'TELÉFONO',
            'type': 'tel' 
        })
    )

    tipo_pago = forms.ChoiceField(
        choices=[('', '--- Seleccione un tipo de pago (Opcional) ---')] + TipoPago.choices,
        required=False, 
        label="Tipo de Pago"
    )
    
    tipo_envio = forms.ChoiceField(
        choices=TipoEnvio.choices, 
        label="Método de Envío",
        initial=TipoEnvio.RECOGIDA_TIENDA 
    )
    
    direccion_envio = forms.CharField(
        max_length=255, 
        required=False, 
        label="Dirección de Envío",
        widget=forms.TextInput(attrs={'placeholder': 'DIRECCIÓN ENVÍO'})
    )


    def clean_password2(self):
        """
        Valida que la segunda contraseña coincida con la primera.
        Si no coinciden, lanza un error específico.
        """
        cd = self.cleaned_data
        password = cd.get('password')
        password2 = cd.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError('Las contraseñas no coinciden. Por favor, revísalas.')
        
        return password2

    def clean(self):
        """
        Valida la lógica condicional: La dirección de envío es obligatoria 
        si el tipo de envío NO es 'RECOGIDA_TIENDA'.
        """
        cleaned_data = super().clean()
        
        tipo_envio = cleaned_data.get("tipo_envio")
        direccion_envio = cleaned_data.get("direccion_envio")
        
        if tipo_envio and tipo_envio != TipoEnvio.RECOGIDA_TIENDA:
            if not direccion_envio:
                self.add_error('direccion_envio', 'Este campo es obligatorio al seleccionar Envío a Domicilio.')

        return cleaned_data


    def save(self):
        
        cd = self.cleaned_data
        
        usuario = Usuario.objects.create(
            nombre=cd['nombre'],
            apellidos=cd['apellidos'],
            corre_electronico=cd['corre_electronico']
        )
        usuario.set_password(cd['password'])
        usuario.save()

        tipo_pago_final = cd.get('tipo_pago') or TipoPago.PASARELA_PAGO 
        
        cliente = UsuarioCliente.objects.create(
            usuario=usuario, 
            telefono=cd.get('telefono', ''), 
            direccion_envio=cd.get('direccion_envio', ''), 
            tipo_pago=tipo_pago_final,
            tipo_envio=cd['tipo_envio']
        )
        
        return cliente