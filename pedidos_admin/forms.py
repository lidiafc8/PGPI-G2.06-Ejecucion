from django import forms
from home.models import Pedido

ESTADO_CHOICES = [
    ('PEDIDO', 'Pedido solicitado'),
    ('ENVIADO', 'Enviado'),
    ('ENTREGADO', 'Entregado')
]

class PedidoEstadoForm(forms.ModelForm):
    """
    Formulario para que el administrador actualice el estado de un pedido.
    """
    class Meta:        
        model = Pedido
        fields = ['estado'] 
        widgets = {
            'estado': forms.Select(choices=ESTADO_CHOICES, attrs={'class': 'input-style'}),
        }
        labels = {
            'estado': 'Estado Actual del Pedido',
        }
        
    """def clean_estado(self):
        
        Validación: Evita cambiar el estado si ya está ENTREGADO.
        
        estado = self.cleaned_data.get('estado')
        if self.instance and self.instance.estado == 'ENTREGADO' and estado != 'ENTREGADO':
             if estado != self.instance.estado: 
                raise forms.ValidationError(
                    "Un pedido marcado como Entregado no puede cambiarse a otro estado."
                )
        
        return estado"""