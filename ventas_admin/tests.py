from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from django.contrib.auth import get_user_model

from home.models import UsuarioCliente, Pedido, EstadoPedido

User = get_user_model()


class VentasAdminTests(TestCase):
	def setUp(self):
		# create a staff user
		self.staff = User.objects.create_superuser('staff@example.com', 'staffpass', nombre='Staff', apellidos='User')

		# create two clients
		self.u1 = User.objects.create_user('c1@example.com', 'pass1', nombre='C1', apellidos='One')
		self.c1 = UsuarioCliente.objects.create(usuario=self.u1)

		self.u2 = User.objects.create_user('c2@example.com', 'pass2', nombre='C2', apellidos='Two')
		self.c2 = UsuarioCliente.objects.create(usuario=self.u2)

		# create pedidos: two for c1 and one for c2, all ENTREGADO
		now = timezone.now()
		# Crear pedidos indicando subtotal_importe para que la lógica de save calcule total_importe correctamente
		# (subtotal + coste_envio). Usamos subtotales que den los totales esperados
		self.p1 = Pedido.objects.create(usuario_cliente=self.c1, subtotal_importe=Decimal('5.00'), estado=EstadoPedido.ENTREGADO, correo_electronico=self.u1.corre_electronico)
		self.p1.fecha_creacion = now
		self.p1.save()

		self.p2 = Pedido.objects.create(usuario_cliente=self.c1, subtotal_importe=Decimal('15.00'), estado=EstadoPedido.ENTREGADO, correo_electronico=self.u1.corre_electronico)
		self.p2.fecha_creacion = now
		self.p2.save()

		self.p3 = Pedido.objects.create(usuario_cliente=self.c2, subtotal_importe=Decimal('0.50'), estado=EstadoPedido.ENTREGADO, correo_electronico=self.u2.corre_electronico)
		self.p3.fecha_creacion = now
		self.p3.save()

	def test_non_staff_redirects_to_home(self):
		url = reverse('ventas_admin_index')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 302)
		self.assertEqual(resp.url, reverse('home'))

	def test_staff_sees_sales_and_totals(self):
		self.client.force_login(self.staff)
		url = reverse('ventas_admin_index')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertIn('ventas', resp.context)
		self.assertIn('clientes', resp.context)
		self.assertIn('total_ganancias', resp.context)
		self.assertIn('total_ventas', resp.context)

		self.assertEqual(resp.context['total_ventas'], 3)
		# Calcular el total esperado a partir de los pedidos en la BD (comportamiento actual del modelo)
		from home.models import Pedido
		expected_total = sum((p.total_importe for p in Pedido.objects.filter(estado=EstadoPedido.ENTREGADO)), Decimal('0.00'))
		self.assertEqual(resp.context['total_ganancias'], expected_total)

	def test_filter_by_cliente(self):
		self.client.force_login(self.staff)
		url = reverse('ventas_admin_index') + f'?cliente={self.c1.id}'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		ventas = resp.context['ventas']
		self.assertEqual(len(ventas), 2)
		self.assertTrue(all(p.usuario_cliente == self.c1 for p in ventas))

	def test_filter_by_date_range(self):
		self.client.force_login(self.staff)
		today = timezone.now().date()
		url = reverse('ventas_admin_index') + f'?fecha_inicio={today}&fecha_fin={today}'
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		ventas = resp.context['ventas']
		self.assertEqual(len(ventas), 3)
