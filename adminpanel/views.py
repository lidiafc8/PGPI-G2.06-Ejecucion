from django.shortcuts import redirect, render

def index(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('home')
    return render(request, 'adminpanel/index.html')
