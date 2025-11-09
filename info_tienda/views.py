from django.shortcuts import render

def index(request):
    return render(request, 'info_tienda/index.html')
