from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json

from django.contrib.auth import get_user_model

from home.models import Producto, Seccion, Categoria

User = get_user_model()

class CatalogoAdminViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.staff_user = User.objects.create_user(
            corre_electronico='admin@example.com', password='pass', nombre='Admin', apellidos='One', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            corre_electronico='user@example.com', password='pass', nombre='User', apellidos='Two', is_staff=False
        )

        gif = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        self.image = SimpleUploadedFile('img.gif', gif, content_type='image/gif')

        self.p1 = Producto.objects.create(
            nombre='P1', descripcion='d', departamento='D', seccion=Seccion.HERRAMIENTAS_MANUALES,
            fabricante='F', categoria=Categoria.CORTE_Y_PODA, precio=Decimal('5.00'), stock=10, imagen=self.image
        )
        self.p2 = Producto.objects.create(
            nombre='P2', descripcion='d2', departamento='D', seccion=Seccion.HERRAMIENTAS_MANUALES,
            fabricante='F2', categoria=Categoria.CORTE_Y_PODA, precio=Decimal('6.00'), stock=8, imagen=self.image
        )

    def test_lista_productos_redirects_non_staff(self):
        resp = self.client.get(reverse('lista_productos'))

        self.assertEqual(resp.status_code, 302)

    def test_lista_productos_shows_for_staff(self):
        self.client.force_login(self.staff_user)
        resp = self.client.get(reverse('lista_productos'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('productos', resp.context)

    def test_anadir_producto_creates_product(self):
        self.client.force_login(self.staff_user)
        url = reverse('anadir_producto')
        data = {
            'nombre': 'Nuevo',
            'descripcion': 'desc',
            'departamento': 'DEP',
            'seccion': Seccion.HERRAMIENTAS_MANUALES,
            'fabricante': 'F',
            'categoria': Categoria.CORTE_Y_PODA,
            'precio': '12.50',
            'stock': '3',
            'esta_agotado': False,
            'esta_destacado': False,
        }
        data_files = {'imagen': self.image}

        resp = self.client.post(url, data=data, files={'imagen': self.image}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Producto.objects.filter(nombre='Nuevo').exists())

    def test_editar_producto_updates(self):
        self.client.force_login(self.staff_user)
        url = reverse('editar_producto', args=[self.p1.id])
        data = {
            'nombre': 'P1-edited',
            'descripcion': self.p1.descripcion,
            'departamento': self.p1.departamento,
            'seccion': self.p1.seccion,
            'fabricante': self.p1.fabricante,
            'categoria': self.p1.categoria,
            'precio': str(self.p1.precio),
            'stock': str(self.p1.stock),
            'esta_agotado': False,
            'esta_destacado': False,
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.nombre, 'P1-edited')

    def test_eliminar_producto_posts_delete(self):
        self.client.force_login(self.staff_user)
        url = reverse('eliminar_producto', args=[self.p2.id])

        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        post_resp = self.client.post(url, follow=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertFalse(Producto.objects.filter(id=self.p2.id).exists())

    def test_guardar_orden_productos_updates_order(self):
        self.client.force_login(self.staff_user)
        url = reverse('guardar_orden_productos')
        ids = [self.p2.id, self.p1.id]
        resp = self.client.post(url, data=json.dumps({'orden_productos': ids}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        p2 = Producto.objects.get(id=self.p2.id)
        p1 = Producto.objects.get(id=self.p1.id)
        self.assertEqual(p2.orden, 1)
        self.assertEqual(p1.orden, 2)

    def test_cargar_categorias_for_staff(self):
        self.client.force_login(self.staff_user)
        url = reverse('cargar_categorias') + '?seccion_valor=HERRAMIENTAS_MANUALES'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        j = resp.json()
        self.assertIn('categorias', j)
        self.assertTrue(isinstance(j['categorias'], list))

    def test_cargar_categorias_redirects_non_staff(self):
        resp = self.client.get(reverse('cargar_categorias') + '?seccion_valor=HERRAMIENTAS_MANUALES')
        self.assertEqual(resp.status_code, 302)
from django.test import TestCase

