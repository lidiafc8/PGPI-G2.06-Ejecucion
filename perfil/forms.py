from django import forms
from django.contrib.auth import get_user_model

# Importa tu modelo de perfil de cliente y cualquier otro modelo necesario (e.g., Administrador)
# Asegúrate de que esta ruta sea correcta:
from home.models import UsuarioCliente 

# Obtener tu modelo de usuario personalizado
Usuario = get_user_model() 

# --- Formulario para actualizar los datos base del Usuario (Admin y Cliente) ---
class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        # 🟢 IMPORTANTE: Usamos first_name y last_name para coincidir con el modelo base de Django/Custom User
        fields = ['first_name', 'last_name', 'email'] 
        
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'NOMBRE', 'class': 'w-full outline-none'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'APELLIDOS', 'class': 'w-full outline-none'}),
            'email': forms.EmailInput(attrs={'placeholder': 'CORREO ELECTRÓNICO', 'class': 'w-full outline-none', 'readonly': 'readonly'}),
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