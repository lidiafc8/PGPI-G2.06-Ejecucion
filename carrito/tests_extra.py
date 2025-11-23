from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from django.contrib.auth import get_user_model

from home.models import (
    Producto, UsuarioCliente, CestaCompra, ItemCestaCompra, Tarjeta
)

User = get_user_model()


class CarritoExtraTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(corre_electronico='ce@test.com', password='p', nombre='C', apellidos='E')
        self.cliente = UsuarioCliente.objects.create(usuario=self.user)

        # create a product
        self.producto = Producto.objects.create(
            nombre='P', descripcion='d', departamento='D', seccion='HERRAMIENTAS_MANUALES',
            fabricante='F', categoria='CORTE_Y_PODA', precio=Decimal('10.00'), stock=10
        )

    def test_checkout_parses_saved_address_and_shows_tarjetas(self):
        # prepare cliente with direccion_envio in a format that exercises parsing
        self.cliente.direccion_envio = 'Calle Falsa 123, 41012 Sevilla, España'
        self.cliente.telefono = '600111222'
        self.cliente.save()

        # create a saved tarjeta
        tarjeta = Tarjeta(usuario_cliente=self.cliente)
        tarjeta.set_card_details('4444333322221111', '12/30', '123')
        tarjeta.save()

        # create cesta with an item
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=self.cliente)
        ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=1, precio_unitario=self.producto.precio)

        self.client.force_login(self.user)
        resp = self.client.get(reverse('carrito:checkout'))
        self.assertEqual(resp.status_code, 200)
        # datos_cliente should contain parsed calle and cp/ciudad
        datos = resp.context['datos_cliente']
        self.assertIn('direccion_calle', datos)
        self.assertIn('direccion_ciudad', datos)

    def test_procesar_pago_invalid_shipping_redirects_to_checkout(self):
        # create cesta and item
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=self.cliente)
        ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=1, precio_unitario=self.producto.precio)

        self.client.force_login(self.user)
        data = {
            'shipping_option': 'invalid',
            'payment_method': 'gateway',
            'contact_email': 'x@x.com',
            'contact_phone': '600',
            'direccion_calle': 'C',
            'direccion_ciudad': 'Ci',
            'direccion_cp': '00000',
            'direccion_pais': 'ES',
            'card_number': '1234567812345678',
            'expiry_date': '12/25',
            'cvv': '123',
        }
        resp = self.client.post(reverse('carrito:procesar_pago'), data)
        # invalid shipping should redirect back to checkout
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('carrito:checkout'), resp.url)

    def test_procesar_pago_invalid_payment_redirects_to_checkout(self):
        cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=self.cliente)
        ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=1, precio_unitario=self.producto.precio)

        self.client.force_login(self.user)
        data = {
            'shipping_option': 'standard',
            'payment_method': 'invalid',
            'contact_email': 'x@x.com',
            'contact_phone': '600',
            'direccion_calle': 'C',
            'direccion_ciudad': 'Ci',
            'direccion_cp': '00000',
            'direccion_pais': 'ES',
        }
        resp = self.client.post(reverse('carrito:procesar_pago'), data)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('carrito:checkout'), resp.url)

    def test_compra_finalizada_renders(self):
        resp = self.client.get(reverse('carrito:fin_compra'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('mensaje_final', resp.context)
