from django.shortcuts import render, redirect
from django.contrib.auth import login, logout # Necesitas 'login' para iniciar la sesión
from .forms import ClienteAuthenticationForm # Importar tu formulario personalizado

# Asumo que esta es la vista que está enlazada a la URL de login
def login_view(request):
    
    if request.method == 'POST':
        # 1. Instanciar el formulario con los datos recibidos (POST)
        # Es crucial pasar request como argumento al instanciar el formulario,
        # ya que ClienteAuthenticationForm lo requiere (debido a que hereda de AuthenticationForm).
        form = ClienteAuthenticationForm(request=request, data=request.POST) 
        
        # 2. Iniciar el proceso de validación/autenticación
        if form.is_valid(): 
            
            # Si el formulario es válido, significa que ClienteAuthenticationForm.clean() 
            # se ejecutó, que authenticate() tuvo éxito y que el usuario está activo.
            
            # El usuario autenticado está guardado en form.get_user()
            user = form.get_user()
            
            # 3. CRÍTICO: Iniciar la sesión
            # Esto establece la sesión de Django, el usuario queda 'logueado'.
            login(request, user) 
            
            # Redirigir a la página principal después de un inicio de sesión exitoso
            return redirect('home') 

        # Si el formulario NO es válido, el error ya está en el objeto 'form'
        # y se re-renderiza automáticamente.
        
    else:
        # Petición GET: Mostrar el formulario vacío por primera vez
        form = ClienteAuthenticationForm(request=request)

    # Renderizar la plantilla (tanto para GET como si el POST falló la validación)
    return render(request, 'login.html', {'form': form})

# (Opcional) La vista de logout es simple:
def logout_view(request):
    logout(request)
    return redirect('home') # O donde quieras redirigir