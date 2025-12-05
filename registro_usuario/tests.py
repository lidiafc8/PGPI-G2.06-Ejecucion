from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model

from home.models import UsuarioCliente

User = get_user_model()

class RegistroUsuarioTests(TestCase):
	def test_get_shows_form(self):
		url = reverse('registro:registro')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn('form', resp.context)

	def test_post_valid_creates_user_and_logs_in(self):
		url = reverse('registro:registro')
		data = {
			'nombre': 'Prueba',
			'apellidos': 'Usuario',
			'corre_electronico': 'nuevo@example.com',

			'password': 'Un1qu3P@ssw0rd!',
			'password2': 'Un1qu3P@ssw0rd!',
			'telefono': '600000000',
			'tipo_envio': 'RECOGIDA_TIENDA',
		}

		resp = self.client.post(url, data, follow=True)

		self.assertEqual(resp.status_code, 200)

		user = User.objects.filter(corre_electronico='nuevo@example.com').first()
		self.assertIsNotNone(user)
		cliente = UsuarioCliente.objects.filter(usuario=user).first()
		self.assertIsNotNone(cliente)

		messages = [m.message for m in get_messages(resp.wsgi_request)]
		self.assertTrue(
			any('Tu cuenta se ha creado' in m for m in messages)
			or any('Cuenta creada, pero no se pudo iniciar sesión automáticamente' in m for m in messages)
		)

	def test_post_invalid_shows_errors_and_does_not_create(self):

		url = reverse('registro:registro')
		data = {
			'nombre': 'Prueba',
			'apellidos': 'Usuario',
			'corre_electronico': 'dup@example.com',
			'password': 'password123',
			'password2': 'different',
			'tipo_envio': 'RECOGIDA_TIENDA',
		}
		resp = self.client.post(url, data)

		self.assertEqual(resp.status_code, 200)
		self.assertIn('form', resp.context)
		form = resp.context['form']
		self.assertTrue(form.errors)

		self.assertFalse(User.objects.filter(corre_electronico='dup@example.com').exists())
