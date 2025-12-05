from django.test import TestCase, Client
from django.urls import reverse

from django.contrib.auth import get_user_model

User = get_user_model()

class AdminPanelIndexViewTest(TestCase):

    def setUp(self):
        self.client = Client()

        self.admin_url = reverse('adminpanel:adminpanel_index')

        self.home_url = reverse('home')

        self.staff_user = User.objects.create_user(
            corre_electronico='staff@test.com',
            password='testpassword',
            nombre='Admin',
            apellidos='Staff',
            is_staff=True
        )

        self.regular_user = User.objects.create_user(
            corre_electronico='regular@test.com',
            password='testpassword',
            nombre='Regular',
            apellidos='User',
            is_staff=False
        )

    def test_1_unauthenticated_user_is_redirected(self):
        """Verifica que un usuario anónimo sea redirigido a 'home'."""
        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(response, self.home_url, status_code=302, target_status_code=200)

    def test_2_authenticated_non_staff_user_is_redirected(self):
        """Verifica que un usuario logueado pero no staff sea redirigido a 'home'."""
        self.client.login(corre_electronico='regular@test.com', password='testpassword')
        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 302)

        self.assertRedirects(response, self.home_url, status_code=302, target_status_code=200)

    def test_3_authenticated_staff_user_has_access(self):
        """Verifica que un usuario logueado y staff acceda correctamente (código 200)."""
        self.client.login(corre_electronico='staff@test.com', password='testpassword')
        response = self.client.get(self.admin_url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'adminpanel/index.html')
