

from django.contrib.auth.backends import BaseBackend
from home.models import Usuario # Importa tu modelo Usuario
from django.contrib.auth.hashers import check_password # Necesario para verificar la clave

class ClienteBackend(BaseBackend):
    
    # Este método es llamado por la función authenticate()
    def authenticate(self, request, username=None, password=None):
        try:
            # 1. Busca el usuario por el campo USERNAME_FIELD ('corre_electronico')
            # Recuerda que el formulario lo pasa como 'username' a authenticate()
            user = Usuario.objects.get(corre_electronico=username)
        except Usuario.DoesNotExist:
            # Si el correo no existe, devuelve None
            return None

        # 2. Verifica la contraseña usando tu método check_password
        # El user.clave contiene el hash; 'password' es la clave en texto plano.
        if user.check_password(password):
            # 3. Si las claves coinciden y el usuario está activo (propiedad requerida)
            if user.is_active: 
                return user
            # Si no está activo, puedes retornar None o lanzar una excepción
            return None 
        
        # Si la contraseña no coincide, devuelve None
        return None

    # Este método es necesario para que Django sepa cómo recuperar al usuario de la sesión
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None