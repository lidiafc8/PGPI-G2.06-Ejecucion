from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .backends import ClienteBackend

User = get_user_model()

class ClienteBackendTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(corre_electronico='u@test.com', password='secret', nombre='U', apellidos='T')
		self.backend = ClienteBackend()

	def test_authenticate_returns_user_with_correct_credentials(self):
		user = self.backend.authenticate(None, username='u@test.com', password='secret')
		self.assertIsNotNone(user)
		self.assertEqual(user.pk, self.user.pk)

	def test_authenticate_none_with_wrong_password(self):
		user = self.backend.authenticate(None, username='u@test.com', password='wrong')
		self.assertIsNone(user)

	def test_get_user(self):
		u = self.backend.get_user(self.user.pk)
		self.assertEqual(u.pk, self.user.pk)

class InicioSesionViewsTest(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(corre_electronico='user1@example.com', password='pw', nombre='Name', apellidos='A')
		self.staff = User.objects.create_user(corre_electronico='staff@example.com', password='pw', nombre='Staff', apellidos='B', is_staff=True)
		self.superu = User.objects.create_superuser(corre_electronico='super@example.com', password='pw')

	def test_login_view_get_shows_form(self):
		url = reverse('inicio_sesion:login')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn('form', resp.context)

	def test_login_view_post_logs_in_and_redirects(self):
		url = reverse('inicio_sesion:login')
		resp = self.client.post(url, {'username': 'user1@example.com', 'password': 'pw'})

		self.assertEqual(resp.status_code, 302)
		self.assertIn(reverse('inicio_sesion:post_login_redirect'), resp['Location'])

	def test_login_view_already_authenticated_redirects(self):
		self.client.force_login(self.user)
		url = reverse('inicio_sesion:login')
		resp = self.client.get(url)

		self.assertEqual(resp.status_code, 302)

	def test_post_login_redirect_for_regular_user(self):
		self.client.force_login(self.user)
		url = reverse('inicio_sesion:post_login_redirect')
		resp = self.client.get(url)

		self.assertEqual(resp.status_code, 302)
		self.assertTrue(resp['Location'].endswith('/'))

	def test_post_login_redirect_for_admins(self):
		self.client.force_login(self.superu)
		url = reverse('inicio_sesion:post_login_redirect')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)

	def test_logout_redirects_home(self):
		url = reverse('inicio_sesion:logout')

		self.client.force_login(self.user)
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)

	def test_cambio_rol_behaviour(self):
		url = reverse('inicio_sesion:cambio_rol')

		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)

		self.client.force_login(self.user)
		resp2 = self.client.get(url)
		self.assertEqual(resp2.status_code, 302)
		self.assertTrue(resp2['Location'].endswith('/'))

		self.client.force_login(self.staff)
		resp3 = self.client.get(url)
		self.assertEqual(resp3.status_code, 302)

