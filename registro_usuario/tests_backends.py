from django.test import TestCase
from django.contrib.auth import get_user_model

from home.models import Usuario


class RegistroBackendsTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        # create user using Usuario model
        self.user = Usuario.objects.create(corre_electronico='rb@test.com', nombre='RB', apellidos='T')
        self.user.set_password('secret')
        self.user.save()

    def test_authenticate_with_correct_credentials(self):
        from registro_usuario.backends import ClienteBackend

        backend = ClienteBackend()
        user = backend.authenticate(None, username='rb@test.com', password='secret')
        self.assertIsNotNone(user)
        self.assertEqual(user.corre_electronico, 'rb@test.com')

    def test_authenticate_with_wrong_password_returns_none(self):
        from registro_usuario.backends import ClienteBackend

        backend = ClienteBackend()
        user = backend.authenticate(None, username='rb@test.com', password='wrong')
        self.assertIsNone(user)

    def test_authenticate_with_unknown_username_returns_none(self):
        from registro_usuario.backends import ClienteBackend

        backend = ClienteBackend()
        user = backend.authenticate(None, username='nope@test.com', password='x')
        self.assertIsNone(user)

    def test_get_user_returns_user_or_none(self):
        from registro_usuario.backends import ClienteBackend

        backend = ClienteBackend()
        found = backend.get_user(self.user.pk)
        self.assertIsNotNone(found)
        self.assertEqual(found.corre_electronico, self.user.corre_electronico)

        not_found = backend.get_user(999999)
        self.assertIsNone(not_found)
