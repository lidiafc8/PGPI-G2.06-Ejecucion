from django import forms
from django.contrib.auth import get_user_model

# Importa tu modelo de perfil de cliente y cualquier otro modelo necesario (e.g., Administrador)
# Asegúrate de que esta ruta sea correcta:
from home.models import UsuarioCliente , Usuario

# Obtener tu modelo de usuario personalizado
Usuarios = get_user_model() 

# --- Formulario para actualizar los datos base del Usuario (Admin y Cliente) ---
class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuarios
        # 🟢 CORRECCIÓN: Volvemos a 'email' ya que 'corre_electronico' no existe en este modelo.
        # Asumimos que first_name, last_name, y email son los campos correctos del modelo base/custom.
        fields = ['first_name', 'last_name', 'email'] 
        
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            # Usar 'email' aquí, y asegurarnos de que existe en el objeto Usuario
            'email': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none', 'readonly': 'readonly'}),
        }

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellidos', 'corre_electronico') 
        
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            # Usar 'email' aquí, y asegurarnos de que existe en el objeto Usuario
            'corre_electronico': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none', 'readonly': 'readonly'}),
        }

# --- Formulario para actualizar los datos adicionales del Cliente (SOLO Cliente) ---
class PerfilClienteForm(forms.ModelForm):
    class Meta:
        model = UsuarioCliente
        # Incluye todos los campos de compra/envío de tu modelo UsuarioCliente.
        fields = ['telefono', 'tipo_pago', 'tipo_envio', 'direccion_envio']
        
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'TELÉFONO', 'class': 'w-full outline-none'}),
            'direccion_envio': forms.TextInput(attrs={'placeholder': 'DIRECCIÓN ENVÍO', 'class': 'w-full outline-none'}),
            # Widgets para Selects, ajustados a Tailwind CSS
            'tipo_pago': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
            'tipo_envio': forms.Select(attrs={'class': 'w-full outline-none border-none bg-transparent'}),
        }