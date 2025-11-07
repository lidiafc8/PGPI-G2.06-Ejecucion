
from django.shortcuts import render, redirect, get_object_or_404
from home.models import Producto  
from .forms import ProductoForm    



def lista_productos(request):
    
    productos = Producto.objects.all()
    context = {'productos': productos}
    return render(request, 'catalogo_admin/lista_productos.html', context)


def anadir_producto(request):
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES) # request.FILES para imágenes
        
        if form.is_valid():
            form.save() 
            return redirect('lista_productos') 

    else:
        form = ProductoForm() 
        
    return render(request, 'catalogo_admin/anadir_producto.html', {'form': form})

def eliminar_producto(request, pk):
    
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST': 
        producto.delete()
        return redirect('lista_productos') 
    return render(request, 'catalogo_admin/confirmar_eliminar.html', {'producto': producto})


def editar_producto(request, pk):

    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        
        if form.is_valid():
            form.save() 
            return redirect('lista_productos') 

    else:
        form = ProductoForm(instance=producto) 
        
    context = {
        'form': form,
        'producto': producto,
        'es_edicion': True 
    }
    return render(request, 'catalogo_admin/anadir_producto.html', context)

def mostrar_producto(request, pk):

    producto = get_object_or_404(Producto, pk=pk)
    
    context = {'producto': producto}
    return render(request, 'catalogo_admin/mostrar_producto.html', context)

def admin_dashboard(request):
    
    return render(request, 'adminpanel/index.html')