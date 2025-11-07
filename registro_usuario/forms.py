from django import forms
from home.models import Usuario, UsuarioCliente 
# Suponiendo que tienes estos enums/clases definidas para tus choices
# Reemplaza con tus nombres reales si son diferentes:
from home.models import TipoPago, TipoEnvio 

class RegistroUsuarioForm(forms.Form):
    
    nombre = forms.CharField(max_length=100, label="Nombre")
    apellidos = forms.CharField(max_length=200, label="Apellidos")
    corre_electronico = forms.EmailField(max_length=200, label="Correo Electrónico")
    
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar contraseña")
    
    telefono = forms.CharField(
        max_length=15, 
        required=False, 
        label="Teléfono (Opcional)"
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
        label="Dirección de Envío"
    )

    def clean(self):
        """
        Este método se ejecuta después de todas las validaciones de campo.
        Aquí aplicamos la lógica de "si eliges A, entonces B es obligatorio".
        """
        cleaned_data = super().clean()
        
        tipo_envio = cleaned_data.get("tipo_envio")
        direccion_envio = cleaned_data.get("direccion_envio")

        # Lógica: La dirección de envío es OBLIGATORIA si el tipo de envío NO es 'RECOGIDA_TIENDA'
        # Asumiendo que 'ENVIO' es el valor de tu opción de envío a domicilio.
        # Si tienes varios tipos de envío, ajusta la condición.
        
        
        if tipo_envio != TipoEnvio.RECOGIDA_TIENDA:
            if not direccion_envio:
                # Si no hay dirección, lanzamos el error y lo adjuntamos al campo 'direccion_envio'
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
            telefono=cd.get('telefono'), 
            direccion_envio=cd.get('direccion_envio', ''), 
            tipo_pago=tipo_pago_final,
            tipo_envio=cd['tipo_envio']
        )
        
        return cliente