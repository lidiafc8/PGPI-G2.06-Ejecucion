from django.db import models
from home.models import Pedido, EstadoPedido
from django.contrib.auth import get_user_model

class HistorialSeguimiento(models.Model):
    """
    Modelo para registrar cada cambio de estado de un pedido.
    """
    pedido = models.ForeignKey(Pedido, related_name='historial_seguimiento', on_delete=models.CASCADE)
    estado_anterior = models.CharField(max_length=20, verbose_name='Estado Anterior')
    estado_nuevo = models.CharField(max_length=20, choices=EstadoPedido.choices, verbose_name='Nuevo Estado')
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True, null=True, verbose_name='Notas de Seguimiento')
    usuario_admin = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank = True, verbose_name='Usuario Administrador') 

    class Meta:
        ordering = ['-fecha_cambio']
        verbose_name = 'Historial de Seguimiento'
        
        
    def __str__(self):
        return f'Pedido #{self.pedido.id} cambiado de {self.estado_anterior} a {self.estado_nuevo} el {self.fecha_cambio}'