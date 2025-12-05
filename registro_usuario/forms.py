from django import forms
from home.models import Usuario, UsuarioCliente
from home.models import TipoPago, TipoEnvio
from django.core.validators import MinLengthValidator, RegexValidator
from django.contrib.auth import password_validation

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

    def clean_corre_electronico(self):
        email = self.cleaned_data.get('corre_electronico')

        if Usuario.objects.filter(corre_electronico=email).exists():
            raise forms.ValidationError(
                "¡Error! Ya existe una cuenta registrada con este correo electrónico."
            )

        return email

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'CONTRASEÑA'}),
        label="Contraseña",
        validators=[password_validation.validate_password]
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

    direccion_calle = forms.CharField(
        max_length=150,
        required=False,
        label="Calle y Número",
        widget=forms.TextInput(attrs={'placeholder': 'CALLE Y NÚMERO'})
    )

    direccion_cp = forms.CharField(
        max_length=10,
        required=False,
        label="Código Postal",
        widget=forms.TextInput(attrs={'placeholder': 'CÓDIGO POSTAL'})
    )

    direccion_ciudad = forms.CharField(
        max_length=100,
        required=False,
        label="Ciudad",
        widget=forms.TextInput(attrs={'placeholder': 'CIUDAD'})
    )

    direccion_pais = forms.CharField(
        max_length=100,
        required=False,
        label="País",
        widget=forms.TextInput(attrs={'placeholder': 'PAÍS'})
    )

    def clean_password2(self):
        cd = self.cleaned_data
        password = cd.get('password')
        password2 = cd.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError('Las contraseñas no coinciden. Por favor, revísalas.')

        return password2

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        if password:
            try:
                password_validation.validate_password(password, None)
            except forms.ValidationError as error:
                self.add_error('password', error)

        tipo_envio = cleaned_data.get("tipo_envio")

        calle = cleaned_data.get("direccion_calle")
        cp = cleaned_data.get("direccion_cp")
        ciudad = cleaned_data.get("direccion_ciudad")
        pais = cleaned_data.get("direccion_pais")

        if tipo_envio and tipo_envio != TipoEnvio.RECOGIDA_TIENDA:
            mensaje_error = 'Este campo es obligatorio al seleccionar Envío a Domicilio.'

            if not calle:
                self.add_error('direccion_calle', mensaje_error)
            if not cp:
                self.add_error('direccion_cp', mensaje_error)
            if not ciudad:
                self.add_error('direccion_ciudad', mensaje_error)
            if not pais:
                self.add_error('direccion_pais', mensaje_error)

        return cleaned_data

    def save(self):
        cd = self.cleaned_data

        usuario = Usuario(
            nombre=cd['nombre'],
            apellidos=cd['apellidos'],
            corre_electronico=cd['corre_electronico']
        )
        usuario.set_password(cd['password'])
        usuario.save()

        calle = cd.get('direccion_calle', '').strip()
        cp = cd.get('direccion_cp', '').strip()
        ciudad = cd.get('direccion_ciudad', '').strip()
        pais = cd.get('direccion_pais', '').strip()

        if calle or cp or ciudad or pais:
             direccion_envio_final = f"{calle}, {cp}, {ciudad}, {pais}".strip()
        else:
             direccion_envio_final = ""

        tipo_pago_final = cd.get('tipo_pago') or TipoPago.PASARELA_PAGO

        cliente = UsuarioCliente.objects.create(
            usuario=usuario,
            telefono=cd.get('telefono', ''),
            direccion_envio=direccion_envio_final,
            tipo_pago=tipo_pago_final,
            tipo_envio=cd['tipo_envio']
        )

        return cliente
