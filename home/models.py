# home/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password

# --- CLASES CHOICES (SIN CAMBIOS) ---

class TipoPago(models.TextChoices):
    PASARELA_PAGO = 'PASARELA_PAGO',
    CONTRAREEMBOLSO = 'CONTRAREEMBOLSO',
    

class TipoEnvio(models.TextChoices):
    DOMICILIO = 'DOMICILIO',
    RECOGIDA_TIENDA = 'RECOGIDA_TIENDA',

class EstadoPedido(models.TextChoices):
    PAGADO = 'PAGADO',
    ENVIADO = 'ENVIADO', 
    ENTREGADO = 'ENTREGADO',

class Seccion(models.TextChoices):
    HERRAMIENTAS_MANUALES = 'HERRAMIENTAS_MANUALES',
    MAQUINARIA_DE_JARDÍN = 'MAQUINARIA_DE_JARDÍN',
    RIEGO='RIEGO',
    CULTIVO_Y_HUERTO = 'CULTIVO_Y_HUERTO',
    PROTECCION_Y_SEGURIDAD='PROTECCION_Y_SEGURIDAD',
    ACCESORIOS_Y_REPUESTOS='ACCESORIOS_Y_REPUESTOS',
    JARDÍN_Y_EXTERIOR='JARDÍN_Y_EXTERIOR',

class Categoria(models.TextChoices):
    CORTE_Y_PODA = 'CORTE_Y_PODA',
    LABRANZA_Y_PLANTACION = 'LABRANZA_Y_PLANTACION',
    RIEGO_MANUAL='RIEGO_MANUAL',
    CORTACESPEDES_Y_DESBROZADORAS = 'CORTACESPEDES_Y_DESBROZADORAS',
    CORTASETOS_Y_MOTOSIERRAS='CORTASETOS_Y_MOTOSIERRAS',
    SOPLADORES_Y_TRITURADORES='SOPLADORES_Y_TRITURADORES',
    RIEGO_AUTOMATICO='RIEGO_AUTOMATICO',
    MANGUERAS='MANGUERAS',
    MACETAS_E_INVERNADEROS='MACETAS_E_INVERNADEROS',
    ABONOS_Y_SUSTRATOS='ABONOS_Y_SUSTRATOS',
    GUANTES_Y_ROPA_PROTECCION='GUANTES_Y_ROPA_PROTECCION',
    GAFAS_Y_CASCOS='GAFAS_Y_CASCOS',
    CUCHILLAS_Y_CADENAS='CUCHILLAS_Y_CADENAS',
    BATERIAS_Y_CARGADORES='BATERIAS_Y_CARGADORES',
    MUEBLES_Y_DECORACION='MUEBLES_Y_DECORACION',
    ILUMINACION_EXTERIOR='ILUMINACION_EXTERIOR',

# --- 🚨 CORRECCIÓN ESTRUCTURAL: MANAGER DE USUARIOS ---
class UsuarioManager(BaseUserManager):
    def create_user(self, corre_electronico, clave=None, **extra_fields):
        if not corre_electronico:
            raise ValueError('El correo electrónico es obligatorio')
        user = self.model(
            corre_electronico=self.normalize_email(corre_electronico),
            **extra_fields
        )
        user.set_password(clave)
        user.save(using=self._db)
        return user

    def create_superuser(self, corre_electronico, clave=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        extra_fields.setdefault('nombre', 'Admin')
        extra_fields.setdefault('apellidos', 'Superuser') 

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(corre_electronico, clave, **extra_fields)


class Usuario(models.Model): 
    nombre = models.CharField(max_length=200)
    apellidos = models.CharField(max_length=200)
    corre_electronico = models.EmailField(max_length=200, unique=True)
    clave = models.CharField(max_length=128)

    last_login = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'corre_electronico'
    REQUIRED_FIELDS = ['nombre', 'apellidos'] 

    
    is_active = models.BooleanField(default=True) 
    is_staff = models.BooleanField(default=False) 
    is_superuser = models.BooleanField(default=False)

    @property
    def is_authenticated(self):
        """Retorna True si el usuario ha sido validado correctamente."""
        # Si tienes una lógica de usuario anónimo, podrías verificar la ID o la sesión aquí.
        # Para un usuario que pasa el login, es True.
        return True 

    @property
    def is_anonymous(self):
        """Retorna False para un objeto de usuario real."""
        return False

    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser

    def set_password(self, raw_password):
        self.clave = make_password(raw_password)
        self._password = raw_password 

    def check_password(self, raw_password):
        return check_password(raw_password, self.clave)

    def __str__(self):
        return self.corre_electronico

# --- 🚨 CORRECCIÓN FUNCIONAL: MODELO USUARIOCLIENTE ---
class UsuarioCliente(models.Model):

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    tipo_pago= models.CharField(max_length=20, choices=TipoPago.choices, default=TipoPago.PASARELA_PAGO)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    # 🚨 CORRECCIÓN: Se añade blank=True para que el perfil se pueda crear vacío (soluciona el bug de get_or_create)
    direccion_envio = models.CharField(max_length=255, blank=True) 
    tipo_envio= models.CharField(max_length=20, choices=TipoEnvio.choices, default=TipoEnvio.RECOGIDA_TIENDA)
    
    def __str__(self):
        return self.usuario.nombre

# --- RESTO DE MODELOS (SIN CAMBIOS) ---
class Administrador(models.Model):

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"Admin: {self.usuario.corre_electronico}"

class Producto(models.Model):
    nombre= models.CharField(max_length=200)
    descripcion= models.TextField()
    departamento= models.CharField(max_length=200)
    seccion=models.CharField(max_length=50, choices=Seccion.choices)
    fabricante=models.CharField(max_length=200)
    categoria=models.CharField(max_length=50, choices=Categoria.choices)
    precio= models.DecimalField(max_digits=10, decimal_places=2)
    stock=models.IntegerField(default=0)
    imagen= models.ImageField(upload_to='', blank=True, null=True)
    esta_agotado= models.BooleanField(default=False)
    esta_destacado= models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0, blank=False, null=False)
    class Meta:
        ordering = ['orden']

    def __str__(self):
        return self.nombre

class CestaCompra(models.Model):

    usuario_cliente= models.OneToOneField('UsuarioCliente', on_delete=models.CASCADE)
    def __str__(self):
        return f'Cesta de {self.usuario_cliente.usuario.corre_electronico}'
    
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
    
    usuario_cliente = models.ForeignKey('UsuarioCliente', on_delete=models.CASCADE) 
    fecha_creacion = models.DateTimeField(auto_now_add=True) 
    estado = models.CharField(max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.PAGADO)
    subtotal_importe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    coste_entrega = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_importe = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    metodo_pago = models.CharField(max_length=20, choices=TipoPago.choices, default=TipoPago.PASARELA_PAGO)
    tipo_envio = models.CharField(max_length=20, choices=TipoEnvio.choices, default=TipoEnvio.RECOGIDA_TIENDA) 
    direccion_envio = models.CharField(max_length=255) 
    correo_electronico = models.EmailField() 
    telefono = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f'Pedido #{self.id} de {self.usuario_cliente.usuario.corre_electronico}' 

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