from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

Usuarios = get_user_model()

class ClienteBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Usuarios.objects.get(corre_electronico=username)
        except Usuarios.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Usuarios.objects.get(pk=user_id)
        except Usuarios.DoesNotExist:
            return None
