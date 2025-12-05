from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from home.models import UsuarioCliente

User = get_user_model()

class ClientesAdminViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.staff_user = User.objects.create_user(
            corre_electronico='admin@example.com', password='pass', nombre='Admin', apellidos='One', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            corre_electronico='user@example.com', password='pass', nombre='User', apellidos='Two', is_staff=False
        )

        self.usuario_cliente = UsuarioCliente.objects.create(usuario=self.normal_user)

    def test_gestion_clientes_redirects_non_staff(self):
        resp = self.client.get(reverse('clientes_admin_index'))

        self.assertEqual(resp.status_code, 302)

        self.client.force_login(self.normal_user)
        resp2 = self.client.get(reverse('clientes_admin_index'))
        self.assertEqual(resp2.status_code, 302)

    def test_gestion_clientes_shows_for_staff(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('clientes_admin_index'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('clientes', resp.context)
        clientes = resp.context['clientes']

        ids = [c.id for c in clientes]
        self.assertIn(self.usuario_cliente.id, ids)

    def test_cliente_eliminar_confirmar_get_and_post(self):
        self.client.force_login(self.staff_user)
        url = reverse('cliente_eliminar_confirmar', args=[self.usuario_cliente.id])

        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        self.assertIn('cliente', get_resp.context)

        post_resp = self.client.post(url, follow=True)
        self.assertEqual(post_resp.status_code, 200)

        self.assertFalse(UsuarioCliente.objects.filter(id=self.usuario_cliente.id).exists())
from django.test import TestCase

