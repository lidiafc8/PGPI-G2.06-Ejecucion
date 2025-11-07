from django import forms
from home.models import Producto 

class ProductoForm(forms.ModelForm):
    
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'departamento', 'seccion', 
            'fabricante', 'categoria', 'precio', 'stock', 'imagen', 
            'esta_agotado', 'esta_destacado'
        ] 
        widgets = {
            
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descripción detallada del producto'}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
            'stock': forms.NumberInput(attrs={'min': '0'}),
            'seccion': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }
         
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción del Producto',
            'departamento': 'Departamento (Área General)',
            'seccion': 'Sección Específica',
            'fabricante': 'Fabricante/Marca',
            'categoria': 'Categoría',
            'precio': 'Precio (€)',
            'stock': 'Unidades en Stock',
            'imagen': 'Foto del Producto',
            'esta_agotado': 'Producto Agotado',
            'esta_destacado': 'Producto Destacado',
        }
