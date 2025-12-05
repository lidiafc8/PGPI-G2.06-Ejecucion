from django.contrib import admin
from home.models import Pedido, ItemPedido, EstadoPedido as EstadoPedidoChoices
from .models import HistorialSeguimiento

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'total')
    extra = 0
    can_delete = False

class HistorialSeguimientoInline(admin.TabularInline):
    model = HistorialSeguimiento
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'fecha_cambio', 'notas', 'usuario_admin')
    extra = 0
    can_delete = False

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario_cliente', 'fecha_creacion', 'estado', 'total_importe', 'metodo_pago', 'tipo_envio', 'direccion_envio')
    list_filter = ('estado', 'metodo_pago', 'tipo_envio', 'fecha_creacion')
    search_fields = ('id', 'usuario_cliente__usuario__corre_electronico', 'direccion_envio')
    readonly_fields = ('usuario_cliente', 'fecha_creacion', 'subtotal_importe', 'coste_entrega', 'total_importe')
    inlines = [ItemPedidoInline, HistorialSeguimientoInline]
    fieldsets = (
        (None, {
            'fields': ('usuario_cliente', 'fecha_creacion', 'estado')
        }),
        ('Datos de Contacto', {
            'fields': ('direccion_envio', 'correo_electronico', 'telefono')
        }),
        ('Información de Pago y Envío', {
            'fields': ('subtotal_importe', 'coste_entrega', 'total_importe', 'metodo_pago', 'tipo_envio')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change and 'estado' in form.changed_data:
            estado_anterior = form.initial.get('estado')
            estado_nuevo = obj.estado
            HistorialSeguimiento.objects.create(
                    pedido=obj,
                    estado_anterior=estado_anterior,
                    estado_nuevo=estado_nuevo,
                    notas = f"Actualizado por el administrador {request.user.username}",
                    usuario_admin=request.user
                )
        super().save_model(request, obj, form, change)
