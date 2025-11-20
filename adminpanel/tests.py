from django.test import TestCase, Client
from django.urls import reverse
# Importar la función para obtener el modelo de usuario personalizado
from django.contrib.auth import get_user_model 

# Obtener el modelo de usuario (esto resuelve tu error anterior)
User = get_user_model() 

class AdminPanelIndexViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # URL de la vista que estamos probando (Usando el namespace 'adminpanel')
        self.admin_url = reverse('adminpanel:adminpanel_index') 
        
        # URL de redirección
        self.home_url = reverse('home')
        
        # 1. Crear usuario Staff (DEBE tener acceso)
        self.staff_user = User.objects.create_user(
            corre_electronico='staff@test.com', 
            password='testpassword',
            nombre='Admin',
            apellidos='Staff', 
            is_staff=True
        )
        
        # 2. Crear usuario Regular (NO DEBE tener acceso)
        self.regular_user = User.objects.create_user(
            corre_electronico='regular@test.com', 
            password='testpassword',
            nombre='Regular',
            apellidos='User',
            is_staff=False
        )

    # --- Test Cases ---

    ## Caso 1: Usuario No Autenticado
    def test_1_unauthenticated_user_is_redirected(self):
        """Verifica que un usuario anónimo sea redirigido a 'home'."""
        response = self.client.get(self.admin_url)
        
        # Debe redirigir (código 302)
        self.assertEqual(response.status_code, 302)
        
        # Debe redirigir al destino 'home' (código 200 esperado en el destino)
        self.assertRedirects(response, self.home_url, status_code=302, target_status_code=200) 


    ## Caso 2: Usuario Autenticado PERO No Staff
    def test_2_authenticated_non_staff_user_is_redirected(self):
        """Verifica que un usuario logueado pero no staff sea redirigido a 'home'."""
        self.client.login(corre_electronico='regular@test.com', password='testpassword')
        response = self.client.get(self.admin_url)
        
        # Debe redirigir (código 302)
        self.assertEqual(response.status_code, 302)
        
        # Debe redirigir al destino 'home'
        self.assertRedirects(response, self.home_url, status_code=302, target_status_code=200)


    ## Caso 3: Usuario Autenticado Y Staff (Acceso Permitido)
    def test_3_authenticated_staff_user_has_access(self):
        """Verifica que un usuario logueado y staff acceda correctamente (código 200)."""
        self.client.login(corre_electronico='staff@test.com', password='testpassword')
        response = self.client.get(self.admin_url)
        
        # Debe retornar un código 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Verifica que se use la plantilla correcta
        self.assertTemplateUsed(response, 'adminpanel/index.html')