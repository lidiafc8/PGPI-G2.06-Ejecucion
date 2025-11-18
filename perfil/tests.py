from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from home.models import UsuarioCliente


User = get_user_model()


class PerfilViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@example.com', 'password123', nombre='User', apellidos='Test')
        self.admin = User.objects.create_superuser('admin@example.com', 'adminpass', nombre='Admin', apellidos='Super')

    def test_mi_perfil_requires_login(self):
        url = reverse('perfil:mi_perfil')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_mi_perfil_get_shows_forms_and_creates_profile(self):
        self.client.force_login(self.user)
        url = reverse('perfil:mi_perfil')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('perfil_form', response.context)
        self.assertTrue(response.context.get('es_cliente'))

        # Perfil should be created by view via get_or_create
        perfil = UsuarioCliente.objects.filter(usuario=self.user).first()
        self.assertIsNotNone(perfil)

    def test_mi_perfil_post_valid_updates(self):
        self.client.force_login(self.user)
        url = reverse('perfil:mi_perfil')
        data = {
            'nombre': 'NuevoNombre',
            'apellidos': 'NuevoApellidos',
            'corre_electronico': self.user.corre_electronico,
            'telefono': '123456789',
            'direccion_envio': 'Calle Falsa 123',
            'tipo_pago': 'PASARELA_PAGO',
            'tipo_envio': 'DOMICILIO',
        }

        response = self.client.post(url, data)
        # successful POST redirects back to mi_perfil
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('perfil:mi_perfil'))

        # messages contains success
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('Perfil de Cliente actualizado' in m for m in messages))

        # Data saved
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombre, 'NuevoNombre')
        perfil = UsuarioCliente.objects.get(usuario=self.user)
        self.assertEqual(perfil.telefono, '123456789')
        self.assertEqual(perfil.direccion_envio, 'Calle Falsa 123')

    def test_mi_perfil_post_invalid_shows_error(self):
        self.client.force_login(self.user)
        url = reverse('perfil:mi_perfil')
        data = {
            'nombre': '',  # invalid: blank nombre
            'apellidos': 'X',
            'corre_electronico': self.user.corre_electronico,
            'telefono': '000',
            'direccion_envio': '',
            'tipo_pago': 'PASARELA_PAGO',
            'tipo_envio': 'DOMICILIO',
        }
        response = self.client.post(url, data)
        # invalid POST should not redirect
        self.assertEqual(response.status_code, 200)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('Error al actualizar el perfil' in m for m in messages))

    def test_mi_perfil_redirects_admins_to_admin_perfil(self):
        # admin user (superuser) should be redirected
        self.client.force_login(self.admin)
        url = reverse('perfil:mi_perfil')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('perfil:admin_perfil'))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('Eres Admin' in m for m in messages))

    def test_admin_perfil_get_and_post(self):
        self.client.force_login(self.admin)
        url = reverse('perfil:admin_perfil')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)

        post_data = {
            'nombre': 'AdminNuevo',
            'apellidos': 'Cambios',
            'corre_electronico': self.admin.corre_electronico,
        }
        response = self.client.post(url, post_data)
        # after successful admin save, redirect to adminpanel index
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminpanel:adminpanel_index'))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.nombre, 'AdminNuevo')
from django.test import TestCase

# Create your tests here.
