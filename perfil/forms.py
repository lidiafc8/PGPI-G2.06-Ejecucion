from django import forms
from django.contrib.auth import get_user_model
# Asegúrate de que las importaciones a tus modelos sean correctas
from home.models import UsuarioCliente, Usuario  

Usuarios = get_user_model() 

# ----------------------------------------------------
# CLASES DE USUARIO
# ----------------------------------------------------

class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        fields = ['nombre', 'apellidos', 'corre_electronico'] 
        
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            'corre_electronico': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none', 'readonly': 'readonly'}),
        }

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'corre_electronico') 
        
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'apellidos': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            'corre_electronico': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none', 'readonly': 'readonly'}),
        }

# ----------------------------------------------------
# ✅ CLASE FINAL CORREGIDA: PerfilClienteForm
# ----------------------------------------------------
class PerfilClienteForm(forms.ModelForm):
    
    # 1. El campo es redefinido para ser de tipo CharField

    class Meta:
        model = UsuarioCliente
        fields = ['telefono', 'tipo_pago', 'tipo_envio', 'direccion_envio']
        
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'TELÉFONO', 'class': 'w-full outline-none'}),
            
            # 2. El widget utiliza 'flex-1' para expandirse y permitir la escritura.
            #    Se eliminan los estilos de borde y fondo, ya que se añaden en el template HTML.
            'direccion_envio': forms.TextInput(attrs={
                'placeholder': 'Ej: Calle Principal, 123, 28001 Madrid, España', 
                'class': 'w-full outline-none border-none bg-transparent flex-1', 
            }),
            
            'tipo_pago': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
            'tipo_envio': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
        }

    # 3. Se elimina el método __init__ innecesario.
    # El método __init__ solo es necesario si necesita modificar los campos en tiempo de ejecución.
    # En este caso, ya no es necesario.