from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class ViewsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.root_url = reverse('index')
        cls.home_url = reverse('home')
        cls.root_template = 'frontpage.html'
        cls.home_template = 'homepage.html'
        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_front_page(self):
        response = self.client.get(self.root_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, self.root_template,
                         "index should be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(self.root_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.home_url,
                         "logged-in users should be sent to their home page")
        return

    def test_home_page(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.root_url,
                         "home page shouldn't be available without logging in")

        self.client.force_login(self.usr)
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, self.home_template,
                         "logged-in users should go to their home page")

        return
