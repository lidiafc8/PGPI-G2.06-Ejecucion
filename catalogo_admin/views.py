
from django.shortcuts import render, redirect, get_object_or_404
from home.models import Producto  
from .forms import ProductoForm    
from django.views.decorators.http import require_POST
import json
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import SECCION_CATEGORIA_MAP


def lista_productos(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    producto = get_object_or_404(Producto, pk=pk)
    
    context = {'producto': producto}
    return render(request, 'catalogo_admin/mostrar_producto.html', context)

def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    return render(request, 'adminpanel/index.html')





@require_POST
def guardar_orden_productos(request):
    try:
        
        data = json.loads(request.body)
        orden_productos = data.get('orden_productos')
        
        if not orden_productos:
            return JsonResponse({'success': False, 'message': 'No se recibió la lista de orden.'}, status=400)


        for index, producto_id in enumerate(orden_productos):
            try:

                producto = get_object_or_404(Producto, pk=producto_id)
                producto.orden = index + 1 
                producto.save()
            except Exception as e:
                print(f"Error al actualizar el producto {producto_id}: {e}")
                
        return JsonResponse({'success': True, 'message': 'Orden de productos actualizada exitosamente.'})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Formato JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno del servidor: {e}'}, status=500)
    

def cargar_categorias(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    seccion_valor = request.GET.get('seccion_valor') 

    categorias_validas = SECCION_CATEGORIA_MAP.get(seccion_valor, [])
    categorias_json = [{'nombre': c} for c in categorias_validas]
    
    return JsonResponse({'categorias': categorias_json})