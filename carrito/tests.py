from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from decimal import Decimal
# Importa tus modelos y las clases TextChoices
from home.models import (
    Producto, CestaCompra, UsuarioCliente, ItemCestaCompra, TipoPago, TipoEnvio,
    EstadoPedido, Tarjeta, Pedido, ItemPedido, Seccion, Categoria
)
from . import views 

# Obtener el modelo de usuario personalizado
User = get_user_model() 

# Clase base con la configuración necesaria para el carrito
# carrito/tests.py

class CartBaseTest(TestCase):
    
    # 📌 CORRECCIÓN CLAVE: El primer argumento ahora se llama 'test_instance' para ignorarlo, 
    # y el Manager de Django se pasa implícitamente a través del patch.
    @staticmethod
    def mock_item_cesta_compra_create(test_instance, **kwargs):
        """
        Mockea la creación de ItemCestaCompra.objects.get_or_create.
        'test_instance' es la instancia de CartBaseTest que se pasa implícitamente 
        cuando se usa @patch en un método de Manager.
        """
        
        # Obtenemos el manager real a través de la clase (esto solo funciona si la clase
        # ItemCestaCompra está disponible globalmente, lo cual es el caso por las importaciones)
        from home.models import ItemCestaCompra
        manager = ItemCestaCompra.objects
        
        producto_id = kwargs.get('producto_id')
        producto = kwargs.get('producto')
        
        if producto is None and producto_id:
            producto = Producto.objects.get(id=producto_id)
        
        # Inyecta el precio unitario si es una creación simulada
        if producto and 'defaults' in kwargs and 'precio_unitario' not in kwargs['defaults']:
            kwargs['defaults']['precio_unitario'] = producto.precio
            
        # Ejecuta la función original del manager usando la sintaxis del Manager de Django
        # ¡IMPORTANTE! Aquí llamamos al método real de la DB con los argumentos modificados.
        # Si tienes problemas, considera cambiar a la Opción A del MagicMock para tests unitarios.
        return manager.get_or_create(**kwargs)

    def setUp(self):
        # --- Corrección 2 y 3: Estos atributos deben definirse en el setUp de la clase base ---
        
        # 1. Creación del usuario base
        self.user = User.objects.create_user(
            corre_electronico='test@user.com', password='testpassword', 
            nombre='Test', apellidos='User', is_staff=False
        )
        # 2. Creación del cliente asociado al usuario
        self.cliente = UsuarioCliente.objects.create(
            usuario=self.user,
            tipo_pago=TipoPago.PASARELA_PAGO, 
            tipo_envio=TipoEnvio.RECOGIDA_TIENDA 
        )
        
        # 3. Simular un archivo de imagen
        gif_content = b'GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x00;'
        gif_file = SimpleUploadedFile(
            "test_image.gif", 
            gif_content,
            content_type='image/gif'
        )

        # 4. Creación del producto de prueba
        # 📌 CORRECCIÓN 1: Usar directamente las clases Seccion y Categoria, no Producto.Seccion/Producto.Categoria
        self.producto = Producto.objects.create(
            nombre='Test Product', 
            descripcion='Una descripción de prueba',
            departamento='JARDINERIA',
            seccion=Seccion.HERRAMIENTAS_MANUALES, # << CORRECCIÓN: Usar Seccion en lugar de Producto.Seccion
            fabricante='FabTest',
            categoria=Categoria.CORTE_Y_PODA, # << CORRECCIÓN: Usar Categoria en lugar de Producto.Categoria
            precio=Decimal('10.00'),
            stock=5,
            imagen=gif_file
        )
        
        self.product_url = reverse('carrito:update_cart', args=[self.producto.id])
        self.client = Client()
        try:
            self.home_url = reverse('home:index')
        except:
            self.home_url = '/'

# -----------------------------------------------------------

class ObtenerCestaTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        try:
            self.accessible_url = reverse('home:index')
        except:
            self.accessible_url = '/' 

    def test_cesta_anonima_crea_session_id(self):
        """Verifica que un usuario anónimo cree un session_id y una CestaCompra."""
        
        response = self.client.get(self.accessible_url) 
        
        request = response.wsgi_request 
        request.user = AnonymousUser() 
        
        cesta = views.obtener_cesta_actual(request)
        
        session_id = request.session.get("cesta_id")
        self.assertIsNotNone(session_id)
        
        self.assertTrue(CestaCompra.objects.filter(session_id=session_id).exists())
        self.assertEqual(cesta.session_id, session_id)
        self.assertIsNone(cesta.usuario_cliente)

class UpdateCartTest(CartBaseTest):
    
    # 📌 CORRECCIÓN: Añadir setUp y llamar a super().setUp()
    def setUp(self):
        super().setUp()
        # Crear una única cesta para este cliente (OneToOne)
        self.cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=self.cliente)
    
    # 🌟 CORRECCIÓN 1: Usar MagicMock para simular la respuesta de get_or_create.
    def test_add_item_to_cart(self):
        """Verifica que añadir un item crea o incrementa la cantidad usando la DB de pruebas."""
        self.client.force_login(self.user)

        response = self.client.post(self.product_url, {'action': 'add'})

        self.assertRedirects(response, reverse('carrito:carrito'))
        item = ItemCestaCompra.objects.filter(cesta_compra=self.cesta, producto=self.producto).first()
        self.assertIsNotNone(item)
        self.assertEqual(item.cantidad, 1)

    # 🌟 CORRECCIÓN 2: Simular el incremento de un item existente.
    def test_add_item_increments_quantity(self):
        """Verifica que añadir el mismo producto incremente la cantidad usando la DB."""
        self.client.force_login(self.user)

        # Añadir dos veces
        self.client.post(self.product_url, {'action': 'add'})
        self.client.post(self.product_url, {'action': 'add'})

        item = ItemCestaCompra.objects.get(cesta_compra=self.cesta, producto=self.producto)
        self.assertEqual(item.cantidad, 2)

    def test_add_item_stock_limit(self):
        """Verifica el límite de stock (stock=5) al añadir."""
        self.client.force_login(self.user)

        # Añadir 5 veces (hasta el stock)
        for _ in range(5):
            self.client.post(self.product_url, {'action': 'add'})

        # Intenta añadir una sexta vez
        response = self.client.post(self.product_url, {'action': 'add'})

        messages = list(get_messages(response.wsgi_request))
        self.assertGreaterEqual(len(messages), 1, "Debería haber al menos un mensaje de límite de stock.")

        self.assertEqual(ItemCestaCompra.objects.first().cantidad, 5)

    def test_remove_item_decrements_quantity(self):
        """Verifica que la acción 'remove' decrementa la cantidad."""
        self.client.force_login(self.user)

        # Crear item con cantidad 3
        ItemCestaCompra.objects.create(cesta_compra=self.cesta, producto=self.producto, cantidad=3, precio_unitario=self.producto.precio)

        self.client.post(self.product_url, {'action': 'remove'})

        item = ItemCestaCompra.objects.get(cesta_compra=self.cesta, producto=self.producto)
        self.assertEqual(item.cantidad, 2)

    def test_remove_item_deletes_when_quantity_is_one(self):
        """Verifica que si la cantidad es 1, la acción 'remove' lo elimina."""
        self.client.force_login(self.user)

        ItemCestaCompra.objects.create(cesta_compra=self.cesta, producto=self.producto, cantidad=1, precio_unitario=self.producto.precio)
        self.assertEqual(ItemCestaCompra.objects.count(), 1)

        self.client.post(self.product_url, {'action': 'remove'})

        self.assertEqual(ItemCestaCompra.objects.count(), 0)
        
    def test_remove_non_existent_product_redirects(self):
        """Verifica que intentar eliminar un producto no existente devuelve 404."""
        # 📌 CORRECCIÓN: No necesita setUp ni self.cliente/self.user, se puede dejar sin implementar setUp si no es necesario sobreescribir.
        response = self.client.post(reverse('carrito:update_cart', args=[9999]), {'action': 'remove'})
        self.assertEqual(response.status_code, 404) 

# ---

class ProcesarPagoTest(CartBaseTest):
    
    def setUp(self):
        # 📌 CORRECCIÓN 2: Llama a setUp de la clase base para heredar self.user, self.cliente, self.producto, etc.
        super().setUp() 
        self.procesar_url = reverse('carrito:procesar_pago')
        
        # self.user y self.client ya están definidos y se pueden usar
        self.client.force_login(self.user)
        
        # 1. Crear la CestaCompra para el cliente autenticado
        # Crear o recuperar la cesta (OneToOne)
        self.cesta, _ = CestaCompra.objects.get_or_create(usuario_cliente=self.cliente)
        
        # 2. Llenar la cesta con 1 ítem
        ItemCestaCompra.objects.create(
            cesta_compra=self.cesta,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio # Asegurar que este valor exista
        )
        self.initial_stock = self.producto.stock 
        self.initial_subtotal = Decimal('10.00') 

        # 3. Datos POST válidos
        # Campos que espera la vista 'procesar_pago'
        self.valid_post_data = {
            'shipping_option': 'standard',
            'payment_method': 'gateway',
            'contact_email': 'cliente@example.com',
            'contact_phone': '600111222',
            'direccion_calle': 'Calle Falsa 123',
            'direccion_ciudad': 'Sevilla',
            'direccion_cp': '41012',
            'direccion_pais': 'España',
            'card_number': '1234567812345678',
            'expiry_date': '12/25',
            'cvv': '123',
            'save_card': 'false',
        }
        
    def test_creacion_pedido_exitosa_y_vaciado_cesta(self):
        """Verifica la creación del Pedido, ItemPedido y vaciado de la Cesta."""
        response = self.client.post(self.procesar_url, self.valid_post_data)
        
        self.assertRedirects(response, reverse('carrito:fin_compra'), status_code=302, target_status_code=200)

        # Verificaciones
        self.assertEqual(Pedido.objects.count(), 1)
        self.assertEqual(ItemPedido.objects.count(), 1)
        self.assertEqual(ItemCestaCompra.objects.count(), 0)

    def test_stock_actualizado_correctamente(self):
        """Verifica que el stock del producto se reduzca en la base de datos."""
        self.client.post(self.procesar_url, self.valid_post_data)
        
        producto_actualizado = Producto.objects.get(id=self.producto.id)
        self.assertEqual(producto_actualizado.stock, self.initial_stock - 1)

    def test_fallo_por_stock_insuficiente_revierte_transaccion(self):
        """Verifica que si el stock es insuficiente, se revierta toda la transacción."""
        
        # Aumentar la cantidad en la cesta para superar el stock (stock inicial=5)
        ItemCestaCompra.objects.filter(cesta_compra=self.cesta).update(cantidad=6)

        response = self.client.post(self.procesar_url, self.valid_post_data)

        self.assertRedirects(response, reverse('carrito:carrito'))
        
        # El pedido NO debe crearse
        self.assertEqual(Pedido.objects.count(), 0)

        # El stock no debe cambiar
        producto_sin_cambios = Producto.objects.get(id=self.producto.id)
        self.assertEqual(producto_sin_cambios.stock, self.initial_stock)
        
        # La cesta no debe vaciarse
        self.assertEqual(ItemCestaCompra.objects.count(), 1)

    def test_guardar_tarjeta_autenticado(self):
        """Verifica que una tarjeta se guarde correctamente al finalizar el pago."""
        
        tarjeta_data = self.valid_post_data.copy()
        tarjeta_data.update({
            'card_number': '1234567890123456',
            'save_card': 'on', 
        })
        
        response = self.client.post(self.procesar_url, tarjeta_data)
        
        self.assertEqual(Tarjeta.objects.count(), 1)
        tarjeta = Tarjeta.objects.first()
        self.assertEqual(tarjeta.usuario_cliente, self.cliente)
        self.assertEqual(tarjeta.ultimos_cuatro, '3456')
        
        self.assertRedirects(response, reverse('carrito:fin_compra'))