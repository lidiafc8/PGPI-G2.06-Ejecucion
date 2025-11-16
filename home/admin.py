from django.contrib import admin
from .models import *


admin.site.register(Producto)
admin.site.register(Usuario)
admin.site.register(UsuarioCliente)
admin.site.register(Administrador)
admin.site.register(ItemCestaCompra)
admin.site.register(CestaCompra)
# admin.site.register(ItemPedido)
# admin.site.register(Pedido)