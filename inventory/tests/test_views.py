from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class IndexViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_index_page(self):

        url = reverse('inv_index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('log_in')),
                         "index should not be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name, 'inventory/index.html')
