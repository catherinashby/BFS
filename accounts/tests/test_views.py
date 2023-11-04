from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from ..views import EmailAddrView, RegisterConfirmView, PasswordView
from ..models import User, UserProfile


class SigninViewTest(TestCase):

    url = reverse('access')

    @classmethod
    def setUpTestData(cls):

        cls.usr1 = User.objects.create_user(username='dorothy',
                                            email='dot@kansas.gov',
                                            is_active=True,
                                            password='rubySlippers')
        cls.usr2 = User.objects.create_user(username='evillene',
                                            email='queen@theWest.gov',
                                            is_active=True,
                                            password='flyingMonkeys')
        UserProfile(user=cls.usr2).save()

    def test_access_page(self):
        response = self.client.post(self.url,
                                    {'username': 'dorothy',
                                     'password': 'rubySlippers'})
        # dorothy has no user profile; redirect to profile page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile'))

        response = self.client.post(self.url,
                                    {'username': 'evillene',
                                     'password': 'flyingMonkeys'})
        # evillene has a user profile; redirect to home page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))


class ProfileViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.usr1 = User.objects.create_user(username='dorothy',
                                            email='dot@kansas.gov',
                                            is_active=True,
                                            password='rubySlippers')
        cls.usr2 = User.objects.create_user(username='evillene',
                                            email='deadbeef',
                                            is_active=True,
                                            password='flyingMonkeys')
        UserProfile(user=cls.usr2).save()

    the_url = reverse('profile')
    template = 'accounts/profile.html'

    def test_get(self):

        self.client.force_login(self.usr1)
        response = self.client.get(self.the_url)
        self.assertEqual(response.status_code, 200, "get should succeed")

        bgn = response.content.find(b'id_email')
        end = response.content.find(b'</p>', bgn)
        self.assertIn(self.usr1.email,
                      response.content[bgn:end].decode(),
                      'email should display on page')

    def test_get_with_kludge(self):

        self.client.force_login(self.usr2)
        response = self.client.get(self.the_url)
        self.assertEqual(response.status_code, 200, "get should succeed")

    def test_post(self):

        self.client.force_login(self.usr1)
        response = self.client.post(self.the_url, location='kansas')
        self.assertIn(b'<p>Successfully saved.</p>', response.content,
                      "'Success' message should be visible")


class AtriumViewTest(TestCase):

    the_url = reverse('atrium')

    def test_find_usrname_in_messages(self):

        req = RequestFactory().get(self.the_url)
        setattr(req, 'session', {})
        setattr(req, '_messages', FallbackStorage(req))
        messages.info(req, 'more data')
        messages.success(req, 'another success')
        messages.success(req, 'evillene', extra_tags='username')

        response = EmailAddrView.as_view()(req)
        fm = response.context_data['form']
        self.assertTrue('usrname' in fm.initial.keys(),
                        "username not passed to form")
        self.assertEqual(fm.initial['usrname'], 'evillene',
                         "wrong username found")
        self.assertEqual(response.status_code, 200)

    def test_sends_email(self):

        mail.outbox = []
        response = self.client.post(self.the_url,
                                    {'usrname': "anotherPerson",
                                     'email': "i.am@waiting.4u"})
        self.assertGreater(len(mail.outbox), 0)

        mail.outbox = []
        svc_name = 'JRandom.MyOwn.Net'
        with self.settings(SERVICE_HOSTNAME=svc_name):
            response = self.client.post(self.the_url,
                                        {'usrname': "someoneElse",
                                         'email': "i.am@myPeak.org"})
            self.assertEqual(response.status_code, 302, "Incorrect status")
            email = mail.outbox[0]
            self.assertTrue(svc_name in email.body)

        return


class UserNameViewTest(TestCase):

    the_url = reverse('entrance')
    template = 'accounts/entrance.html'

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username='dorothy',
                                 email='dot@kansas.gov',
                                 is_active=True,
                                 password='rubySlippers')

    def check_messages(self, resp):
        try:
            storage = list(messages.get_messages(resp.wsgi_request))
            msgs = list()   # iteration needed to clear out messages
            for messege in storage:
                msgs.append(messege)
        except:     # noqa
            msgs = None
        return msgs

    def test_page_shown(self):

        response = self.client.get(self.the_url)
        self.assertEqual(response.status_code, 200,
                         "should load entrance page")
        self.assertEqual(response.templates[0].name, self.template)

    def test_post_with_bad_button(self):

        response = self.client.post(self.the_url,
                                    {'pressed': "mitm"})
        self.assertEqual(response.status_code, 200,
                         "should re-load entrance page")
        self.assertEqual(response.templates[0].name, self.template)

    def test_post_with_login_button(self):

        user_name = "dorothy"
        response = self.client.post(self.the_url,
                                    {'username': user_name,
                                     'pressed': "login"})
        # lawrence has an account
        self.assertEqual(response.status_code, 302,
                         "should redirect to collect password")
        self.assertEqual(response.url, reverse('ingress'))
        # username should be passed as a message to next page
        storage = self.check_messages(response)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, user_name)

    def test_post_with_register_button(self):

        user_name = "evillene"
        response = self.client.post(self.the_url,
                                    {'username': user_name,
                                     'pressed': "register"})
        # katya doesn't have an account; should be redirected
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('atrium'))
        # username should be passed as a message to next page
        storage = self.check_messages(response)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, user_name)


class RegisterConfirmViewTest(TestCase):

    template = 'accounts/vestibule.html'
    next_page = reverse('threshold')

    @classmethod
    def setUpTestData(cls):

        s1n = User.objects.create_user(username='some1New',
                                       email='i.am@home.com',
                                       is_active=False)
        s1n.set_unusable_password()
        s1n.save()

        uidb64 = urlsafe_base64_encode(force_bytes(s1n.pk))
        url_token = RegisterConfirmView.reset_url_token
        cls.the_url = '/accounts/vestibule/{}/{}/'.format(uidb64, url_token)
        cls.tkn = default_token_generator.make_token(s1n)

    def test_unmatched_passwords(self):

        sess = self.client.session
        sess[INTERNAL_RESET_SESSION_TOKEN] = self.tkn
        sess.save()

        response = self.client.post(self.the_url,
                                    {'new_password1': "firstWord",
                                     'new_password2': "secondWord"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, self.template,
                         "should load 'invalid' message, not form")
        self.assertTrue(INTERNAL_RESET_SESSION_TOKEN in self.client.session,
                        'token should not be removed on form errors')

    def test_matched_passwords(self):

        sess = self.client.session
        sess[INTERNAL_RESET_SESSION_TOKEN] = self.tkn
        sess.save()

        response = self.client.post(self.the_url,
                                    {'new_password1': "unusable",
                                     'new_password2': "unusable"})

        self.assertEqual(response.status_code, 302,
                         "should redirect to 'threshold' page")
        self.assertEqual(response.url, self.next_page)
        self.assertFalse(INTERNAL_RESET_SESSION_TOKEN in self.client.session,
                         'token should be removed on form success')

        s1n = User.objects.get(username='some1New')
        self.assertTrue(s1n.has_usable_password(), "password wasn't saved")
        self.assertTrue(s1n.is_active, "user wasn't activated")
        return


class PasswordViewTest(TestCase):

    the_url = reverse('ingress')
    template = 'accounts/ingress.html'

    @classmethod
    def setUpTestData(cls):
        cls.usr1 = User.objects.create_user(username='dorothy',
                                            email='dot@kansas.gov',
                                            is_active=True,
                                            password='rubySlippers')
        cls.usr2 = User.objects.create_user(username='evillene',
                                            email='queen@theWest.gov',
                                            is_active=True,
                                            password='flyingMonkeys')
        UserProfile(user=cls.usr2).save()

    def test_finds_usrname_in_messages(self):

        req = RequestFactory().get(self.the_url)
        setattr(req, 'session', {})
        setattr(req, '_messages', FallbackStorage(req))
        messages.info(req, 'more data')
        messages.success(req, 'another success')
        messages.success(req, 'glinda', extra_tags='username')

        response = PasswordView.as_view()(req)
        fm = response.context_data['form']
        self.assertTrue('username' in fm.initial.keys(),
                        "username not passed to form")
        self.assertEqual(fm.initial['username'], 'glinda',
                         "wrong username found")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name[0], self.template,
                         "should load form")

    def test_new_users_sent_to_profile(self):
        self.client.force_login(self.usr1)
        response = self.client.post(self.the_url,
                                    {'username': 'dorothy',
                                     'password': 'rubySlippers'})
        self.assertEqual(response.url, reverse('profile'),
                         "new user should redirect to profile page")
        self.client.logout()

        self.client.force_login(self.usr2)
        response = self.client.post(self.the_url,
                                    {'username': 'evillene',
                                     'password': 'flyingMonkeys'})
        self.assertEqual(response.url, reverse('home'),
                         "returning user should redirect to root (home page)")

        return
