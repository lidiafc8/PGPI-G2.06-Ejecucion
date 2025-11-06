from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class MetodoPago(models.TextChoices):

    TARJETA = 'TARJETA',
    PAYPAL = 'PAYPAL',
    TRANSFERENCIA = 'TRANSFERENCIA',
    CONTRA_ENTREGA = 'CONTRA_ENTREGA',

class Usuario(models.Model):
    nombre= models.CharField(max_length=200)
    apellidos= models.CharField(max_length=200)
    corre_electronico= models.EmailField(max_length=200, unique=True)
    clave= models.CharField(max_length=128)

    def set_password(self, raw_password):
        self.clave = make_password(raw_password)
        self._password = raw_password 

    def check_password(self, raw_password):
        return check_password(raw_password, self.clave)

    def __str__(self):
        return self.correo_electronico

class UsuarioCliente(models.Model):

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    metodo_pago= models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.TARJETA)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion_envio = models.CharField(max_length=255)
    
    def __str__(self):
        return self.usuario.nombre

class Administrador(models.Model):

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Admin: {self.usuario.username}"

class Producto(models.Model):
    nombre= models.CharField(max_length=200)
    descripcion= models.TextField()
    departamento= models.CharField(max_length=200)
    seccion=models.CharField(max_length=200)
    fabricante=models.CharField(max_length=200)
    categoria=models.CharField(max_length=200)
    precio= models.DecimalField(max_digits=10, decimal_places=2)
    stock=models.IntegerField(default=0)
    imagen= models.ImageField(upload_to='productos/', blank=True, null=True)
    esta_agotado= models.BooleanField(default=False)

    def __str__(self):
        return self.nombre
class CestaCompra(models.Model):

    usuario_cliente= models.OneToOneField('UsuarioCliente', on_delete=models.CASCADE)
    def __str__(self):
        return f'Cesta de {self.usuario_cliente.usuario.correo_electronico}'
    
    def get_total_cesta(self):
        return sum(item.total for item in self.items.all())


class ItemCestaCompra(models.Model):

    cesta_compra = models.ForeignKey(CestaCompra, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1) 
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) 
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'

class Pedido(models.Model):
    class EstadoPedido(models.TextChoices):
        PENDIENTE = 'PENDIENTE',
        PROCESANDO = 'PROCESANDO',
        ENVIADO = 'ENVIADO', 
        ENTREGADO = 'ENTREGADO',
        CANCELADO = 'CANCELADO',

    usuario_cliente = models.ForeignKey('UsuarioCliente', on_delete=models.CASCADE) 
    fecha_creacion = models.DateTimeField(auto_now_add=True) 
    estado = models.CharField(max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE)
    subtotal_importe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    coste_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_importe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metodo_pago = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.TARJETA)
    tipo_envio = models.CharField(max_length=50, blank=True) 
    direccion_envio = models.CharField(max_length=255) 
    correo_electronico = models.EmailField() 
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f'Pedido #{self.id} de {self.usuario_cliente.usuario.correo_electronico}' 

class ItemPedido(models.Model):

    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT) 
    
    cantidad = models.PositiveIntegerField(default=1) 
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) 
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    


class Escaparate(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.producto.id)