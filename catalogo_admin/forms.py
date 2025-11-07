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
            
            'nombre': forms.TextInput(attrs={'class': 'input-style'}), 
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descripción detallada del producto', 'class': 'input-style'}),

            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'class': 'input-style'}),
            'stock': forms.NumberInput(attrs={'min': '0', 'class': 'input-style'}),
            'departamento': forms.TextInput(attrs={'class': 'input-style'}), 
            'fabricante': forms.TextInput(attrs={'class': 'input-style'}), 

            'seccion': forms.Select(attrs={'class': 'input-style'}),
       
            'categoria': forms.Select(attrs={'class': 'input-style'}),
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
