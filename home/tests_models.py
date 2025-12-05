from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from decimal import Decimal

from .models import (
    Usuario, UsuarioCliente, Producto, CestaCompra, ItemCestaCompra,
    Pedido, ItemPedido, Tarjeta
)
from .context_processors import productos_en_cesta

User = get_user_model()

class HomeModelsTest(TestCase):
    def setUp(self):
        gif = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        self.image = SimpleUploadedFile('img.gif', gif, content_type='image/gif')

        self.user = User.objects.create_user(corre_electronico='m@test.com', password='p', nombre='M', apellidos='T')
        self.cliente = UsuarioCliente.objects.create(usuario=self.user)

        self.producto = Producto.objects.create(
            nombre='X', descripcion='d', departamento='D', seccion='HERRAMIENTAS_MANUALES',
            fabricante='F', categoria='CORTE_Y_PODA', precio=Decimal('3.50'), stock=10, imagen=self.image
        )

    def test_item_cesta_save_sets_total(self):
        cesta = CestaCompra.objects.create(usuario_cliente=self.cliente)
        item = ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=2, precio_unitario=Decimal('3.50'))

        self.assertEqual(item.total, Decimal('7.00'))

    def test_cesta_get_total_cesta_uses_item_totals(self):
        cesta = CestaCompra.objects.create(usuario_cliente=self.cliente)
        item = ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=2, precio_unitario=Decimal('3.50'))

        expected = item.total * item.cantidad
        self.assertEqual(cesta.get_total_cesta(), expected)

    def test_item_pedido_save_sets_total(self):
        pedido = Pedido.objects.create(usuario_cliente=self.cliente, correo_electronico='c@test.com')
        item = ItemPedido.objects.create(pedido=pedido, producto=self.producto, cantidad=3, precio_unitario=Decimal('2.00'))
        self.assertEqual(item.total, Decimal('6.00'))

    def test_tarjeta_set_and_check(self):
        tarjeta = Tarjeta(usuario_cliente=self.cliente)
        tarjeta.set_card_details('1234567812345678', '12/25', '123')

        self.assertEqual(tarjeta.ultimos_cuatro, '5678')

        self.assertNotEqual(tarjeta.card_hash, '1234567812345678')
        self.assertNotEqual(tarjeta.card_cvv_hash, '123')

        self.assertTrue(tarjeta.check_card('1234567812345678'))
        self.assertTrue(tarjeta.check_cvv('123'))

    def test_usuario_str_and_usuario_cliente_str(self):
        self.assertEqual(str(self.user), self.user.corre_electronico)
        self.assertEqual(str(self.cliente), self.user.nombre)

class ContextProcessorTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(corre_electronico='ctx@test.com', password='p', nombre='Ctx', apellidos='T')
        self.cliente = UsuarioCliente.objects.create(usuario=self.user)
        gif = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        image = SimpleUploadedFile('img.gif', gif, content_type='image/gif')
        self.producto = Producto.objects.create(
            nombre='CTX', descripcion='d', departamento='D', seccion='HERRAMIENTAS_MANUALES',
            fabricante='F', categoria='CORTE_Y_PODA', precio=Decimal('1.00'), stock=5, imagen=image
        )

    def test_productos_en_cesta_anonymous(self):

        req = self.client.get('/') .wsgi_request
        ctx = productos_en_cesta(req)
        self.assertEqual(ctx['total_items_cesta'], 0)

    def test_productos_en_cesta_authenticated(self):

        cesta = CestaCompra.objects.create(usuario_cliente=self.cliente)
        ItemCestaCompra.objects.create(cesta_compra=cesta, producto=self.producto, cantidad=4, precio_unitario=Decimal('1.00'))

        class R: pass
        req = R()
        req.user = self.user
        req.session = {}
        ctx = productos_en_cesta(req)
        self.assertEqual(ctx['total_items_cesta'], 4)
