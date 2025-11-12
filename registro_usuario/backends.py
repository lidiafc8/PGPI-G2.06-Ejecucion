# inicio_sesion/backends.py (Versión SOLICITADA y Corregida)

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from home.models import Usuario 


class ClienteBackend(BaseBackend):
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Usuario.objects.get(corre_electronico=username)
        except Usuario.DoesNotExist:
            return None
            
        if user.check_password(password):
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None