from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from decimal import Decimal
import json

from .models import Producto, UsuarioCliente, Seccion, Categoria, CestaCompra, ItemCestaCompra

User = get_user_model()

class HomeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        gif = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        image = SimpleUploadedFile('img.gif', gif, content_type='image/gif')

        self.prod_featured = Producto.objects.create(
            nombre='Feat', descripcion='d', departamento='D', seccion=Seccion.HERRAMIENTAS_MANUALES,
            fabricante='F', categoria=Categoria.CORTE_Y_PODA, precio=Decimal('12.34'), stock=5, imagen=image, esta_destacado=True
        )
        self.prod_other = Producto.objects.create(
            nombre='Other', descripcion='otro', departamento='D', seccion=Seccion.HERRAMIENTAS_MANUALES,
            fabricante='F2', categoria=Categoria.CORTE_Y_PODA, precio=Decimal('5.00'), stock=3, imagen=image, esta_destacado=False
        )

        self.user = User.objects.create_user(corre_electronico='u@x.com', password='pass', nombre='U', apellidos='X')
        self.usuario_cliente = UsuarioCliente.objects.create(usuario=self.user)

    def test_index_shows_featured_when_no_category(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        self.assertIn('productos_destacados', ctx)
        productos = list(ctx['productos_destacados'])
        self.assertIn(self.prod_featured, productos)
        self.assertNotIn(self.prod_other, productos)

    def test_index_with_category_filters(self):
        url = reverse('productos_por_categoria', args=['CORTE_Y_PODA'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('productos_destacados', resp.context)
        prods = list(resp.context['productos_destacados'])

        self.assertIn(self.prod_featured, prods)
        self.assertIn(self.prod_other, prods)

    def test_detalle_producto_contains_euros_centavos_and_related(self):
        url = reverse('detalle_producto', args=[self.prod_featured.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        prod = resp.context['producto']
        self.assertTrue(hasattr(prod, 'euros'))
        self.assertTrue(hasattr(prod, 'centavos'))
        related = list(resp.context['productos_relacionados'])

        self.assertIn(self.prod_other, related)

    def test_buscar_productos_finds_by_name_and_sets_context(self):
        resp = self.client.get(reverse('buscar'), {'q': 'Feat'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('productos_destacados', resp.context)
        found = list(resp.context['productos_destacados'])
        self.assertIn(self.prod_featured, found)

    def test_agregar_a_cesta_anonymous_creates_session_and_item(self):
        url = reverse('agregar_a_cesta', args=[self.prod_featured.id])
        resp = self.client.post(url, {'cantidad': '2'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data.get('success'))

        session_id = self.client.session.get('cesta_id')
        self.assertIsNotNone(session_id)

        cesta = CestaCompra.objects.filter(session_id=session_id).first()
        self.assertIsNotNone(cesta)
        item = ItemCestaCompra.objects.filter(cesta_compra=cesta, producto=self.prod_featured).first()
        self.assertIsNotNone(item)
        self.assertEqual(item.cantidad, 2)

    def test_agregar_a_cesta_authenticated_uses_usuario_cliente(self):
        self.client.force_login(self.user)
        url = reverse('agregar_a_cesta', args=[self.prod_featured.id])
        resp = self.client.post(url, {'cantidad': '1'})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(data.get('success'))
        cesta = CestaCompra.objects.filter(usuario_cliente=self.usuario_cliente).first()
        self.assertIsNotNone(cesta)
        item = ItemCestaCompra.objects.filter(cesta_compra=cesta, producto=self.prod_featured).first()
        self.assertIsNotNone(item)
        self.assertEqual(item.cantidad, 1)
from django.test import TestCase

