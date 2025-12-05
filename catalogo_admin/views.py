from django.shortcuts import render, redirect, get_object_or_404
from home.models import Producto, Seccion, Categoria
from .forms import ProductoForm, SECCION_CATEGORIA_MAP
from django.views.decorators.http import require_POST
import json
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def lista_productos(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')

    seccion_seleccionada = request.GET.get('seccion')
    categoria_seleccionada = request.GET.get('categoria')
    fabricante_seleccionado = request.GET.get('fabricante')

    if categoria_seleccionada and not seccion_seleccionada:
        for sec, cats in SECCION_CATEGORIA_MAP.items():
            if categoria_seleccionada in cats:
                seccion_seleccionada = sec
                break

    productos = Producto.objects.all().order_by('orden')

    if seccion_seleccionada:
        productos = productos.filter(seccion=seccion_seleccionada)

    if categoria_seleccionada:
        productos = productos.filter(categoria=categoria_seleccionada)

    if fabricante_seleccionado:
        productos = productos.filter(fabricante=fabricante_seleccionado)

    fabricantes_choices = [
        (f, f)
        for f in Producto.objects.values_list('fabricante', flat=True).distinct().order_by('fabricante')
    ]
    fabricantes_list = [f for f, _ in fabricantes_choices]

    categorias_choices = list(Categoria.choices)
    if seccion_seleccionada:
        categorias_validas = SECCION_CATEGORIA_MAP.get(seccion_seleccionada, [])
        categorias_choices = [c for c in categorias_choices if c[0] in categorias_validas]

    context = {
        'productos': productos,

        'seccion_seleccionada': seccion_seleccionada,
        'categoria_seleccionada': categoria_seleccionada,
        'fabricante_seleccionado': fabricante_seleccionado,

        'secciones': list(Seccion.choices),
        'categorias': categorias_choices,
        'fabricantes': fabricantes_list,

        'seccion_categoria_map_json': json.dumps(SECCION_CATEGORIA_MAP),
    }

    return render(request, 'catalogo_admin/lista_productos.html', context)

def anadir_producto(request):
        if request.method == 'POST':
            form = ProductoForm(request.POST, request.FILES)

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
