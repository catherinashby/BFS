import string

from django.test import TestCase

from ..forms import (CustomUserCreationForm, EmailForm,
                     IngressForm, UserNameForm)
from ..models import User


class UserCreationFormTest(TestCase):

    def test_default_password_kludge(self):
        form = CustomUserCreationForm(data={'username': 'evillene',
                                            'password1': 'brandNewDay',
                                            'password2': 'brandNewDay'})
        user = form.save(commit=False)
        self.assertTrue(set(user.email).issubset(string.hexdigits),
                        "kludge should set email equal to hexstring")
        self.assertIsNone(user.pk, "Shouldn't be saved to db yet")
        user = form.save(commit=True)
        self.assertIsNotNone(user.pk, "Should be saved to db now")
        return


class EmailFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='dorothy',
                                 is_active=True,
                                 email='dorothy@kansas.gov',
                                 password='rubySlippers')

    def test_clean_email(self):

        form = EmailForm(data={'email': 'mitm'})
        self.assertEqual(form.errors["email"],
                         ["Enter a valid email address."])
        self.assertEqual(form.errors["usrname"], ["This field is required."])

        form = EmailForm(data={'usrname': '1',
                               'email': 'dorothy@kansas.gov'})
        form.is_valid()  # force validation, to create cleaned_data
        self.assertEqual(form.errors["email"], ["Email in use -- try another"])

        self.assertEqual(User.objects.all().count(), 1, 'only one test user')
        form = EmailForm(data={'usrname': 'evillene',
                               'email': 'i.am@aSite.org'})
        form.is_valid()     # force validation
        self.assertEqual(User.objects.all().count(), 2,
                         'evillene should have been added')

        for who in form.get_users('i.am@aSite.org'):
            self.assertFalse(who.is_active,
                             "should have been saved as inactive")
        return


class IngressFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='dorothy',
                                 is_active=True,
                                 email='dorothy@kansas.gov',
                                 password='rubySlippers')

    def test_bad_password(self):
        form = IngressForm(data={'username': 'dorothy',
                                 'password': 'password'})
        self.assertEqual(form.errors["__all__"],
                         ["Please enter a correct password."])


class UserNameFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='dorothy',
                                 is_active=True,
                                 email='dorothy@kansas.gov',
                                 password='rubySlippers')

    def test_clean(self):

        form = UserNameForm(data={'pressed': 'login',
                                  'username': 'evillene'})
        form.full_clean()   # needed to create cleaned_data
        self.assertEqual(form.errors["__all__"],
                         ["Name not found -- did you want to register?"])

        form = UserNameForm(data={'pressed': 'register',
                                  'username': 'dorothy'})
        form.full_clean()   # needed to create cleaned_data
        self.assertEqual(form.errors["__all__"],
                         ["Already in use -- try another username."])

    def test_clean_pressed(self):

        form = UserNameForm(data={'pressed': 'mitm'})
        self.assertEqual(form.errors["__all__"], ["Unknown action received"])

        form = UserNameForm(data={'pressed': 'register'})
        form.full_clean()   # needed to create cleaned_data
        self.assertEqual(form.cleaned_data["pressed"], 'R')

        form = UserNameForm(data={'pressed': 'login'})
        form.full_clean()   # needed to create cleaned_data
        self.assertEqual(form.cleaned_data["pressed"], 'L')

    def test_clean_username(self):

        form = UserNameForm(data={'pressed': 'invalid',
                                  'username': 'dorothy'})
        form.full_clean()   # needed to create cleaned_data
        self.assertTrue(form.username_found, "Dorothy should be in database!")
