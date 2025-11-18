from django.test import TestCase, Client
from django.urls import reverse


class InfoTiendaViewsTest(TestCase):
	def setUp(self):
		self.client = Client()

	def test_index_renders_template(self):
		# The app is included under namespace 'info_tienda' in project urls
		try:
			url = reverse('info_tienda:info_tienda')
		except Exception:
			# fallback to direct path
			url = '/info_tienda/'

		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# ensure correct template is used
		templates = [t.name for t in resp.templates if t.name]
		self.assertIn('info_tienda/index.html', templates)
