

from django import forms
from home.models import Producto



SECCION_CATEGORIA_MAP = {
    
    'HERRAMIENTAS_MANUALES': ['CORTE_Y_PODA', 'LABRANZA_Y_PLANTACION', 'RIEGO_MANUAL'],
    'MAQUINARIA_DE_JARDÍN': ['CORTACESPEDES_Y_DESBROZADORAS', 'CORTASETOS_Y_MOTOSIERRAS', 'SOPLADORES_Y_TRITURADORES'],
    'RIEGO': ['RIEGO_AUTOMATICO', 'MANGUERAS'], 
    'CULTIVO_Y_HUERTO': ['MACETAS_E_INVERNADEROS', 'ABONOS_Y_SUSTRATOS'],
    'PROTECCION_Y_SEGURIDAD': ['GUANTES_Y_ROPA_PROTECCION', 'GAFAS_Y_CASCOS'],
    'ACCESORIOS_Y_REPUESTOS': ['CUCHILLAS_Y_CADENAS', 'BATERIAS_Y_CARGADORES'], 
    'JARDÍN_Y_EXTERIOR': ['MUEBLES_Y_DECORACION', 'ILUMINACION_EXTERIOR'],
}

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
        
    def clean(self):
       
        cleaned_data = super().clean()
        stock = cleaned_data.get('stock')
        esta_agotado = cleaned_data.get('esta_agotado')

       
        if stock is not None and stock > 0 and esta_agotado:
            self.add_error(
                'esta_agotado', 
                "No puedes marcar como 'Agotado' si el Stock es mayor que 0. Corrige el Stock o desmarca esta opción."
            )
            
        
        if stock is not None and stock == 0 and not esta_agotado:
            self.add_error(
                'esta_agotado', 
               "El Stock es 0. El producto debe marcarse como 'Agotado'."
           )
        seccion_valor = cleaned_data.get('seccion') 
        categoria_valor = cleaned_data.get('categoria') 
        if seccion_valor and categoria_valor:
            categorias_permitidas = SECCION_CATEGORIA_MAP.get(seccion_valor)
                
            if categorias_permitidas is None:
                    self.add_error('seccion', f"Valor de Sección '{seccion_valor}' no reconocido en el sistema.")

            elif categoria_valor not in categorias_permitidas:
                self.add_error('categoria',f"La Categoría '{categoria_valor}' no es válida para la Sección '{seccion_valor}'. Debe ser una de: {', '.join(categorias_permitidas)}")
                    
            return cleaned_data