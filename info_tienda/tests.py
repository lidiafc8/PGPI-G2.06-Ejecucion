from django.test import TestCase, Client
from django.urls import reverse

class InfoTiendaViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_index_renders_template(self):

		try:
			url = reverse('info_tienda:info_tienda')
		except Exception:

			url = '/info_tienda/'

		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)

		templates = [t.name for t in resp.templates if t.name]
		self.assertIn('info_tienda/index.html', templates)
