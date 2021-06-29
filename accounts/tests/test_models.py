from django.test import TestCase

from ..models import User, UserProfile


class ModelsTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_User_object(self):
        """Nothing to test here"""

        pass

    def test_UserProfile_object(self):

        nm = self.usr.get_username()
        txt = 'Profile for {}'.format(nm)
        obj = UserProfile(user=self.usr)
        lbl = '{}'.format(obj)
        self.assertEqual(lbl, txt)
