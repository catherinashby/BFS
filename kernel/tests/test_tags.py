from django.test import RequestFactory, TestCase
from django.template import Context, RequestContext, Template

from ..templatetags.base_tags import *
from accounts.models import User


class BaseTagTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.usr = User.objects.create_user(username='dorothy',
                                           email='dot@kansas.gov',
                                           is_active=True,
                                           password='rubySlippers')

    def test_template_filename(self):
        flnm = 'an .html file'
        cntxt = Context()
        setattr(cntxt, 'template_name', flnm)
        tag = template_filename(cntxt)
        self.assertEqual(tag, flnm, "should return template name")

    def test_user_class(self):
        req = RequestFactory().get('/')
        req.user = self.usr

        cntxt = RequestContext(req)
        cls = user_class(cntxt)
        self.assertEqual(cls, '', "should return empty string")

        req.user.is_staff = True
        cntxt = RequestContext(req)
        cls = user_class(cntxt)
        self.assertEqual(cls, 'staff', "should return 'staff'")

        req.user.is_superuser = True
        cntxt = RequestContext(req)
        cls = user_class(cntxt)
        self.assertEqual(cls, 'superstaff', "should return 'superstaff'")

        req.user.is_staff = False
        cntxt = RequestContext(req)
        cls = user_class(cntxt)
        self.assertEqual(cls, 'super', "should return 'super'")
        return

    def test_user_initials(self):
        req = RequestFactory().get('/')
        req.user = self.usr

        cntxt = RequestContext(req)
        chars = user_initials(cntxt)
        self.assertEqual(chars, '  ', "should return two blanks")

        req.user.first_name = 'Diana'
        cntxt = RequestContext(req)
        chars = user_initials(cntxt)
        self.assertEqual(chars, 'D ', "should return 'D-blank'")

        req.user.last_name = 'Ross'
        cntxt = RequestContext(req)
        chars = user_initials(cntxt)
        self.assertEqual(chars, 'DR', "should return 'DR'")

        req.user.first_name = ''
        cntxt = RequestContext(req)
        chars = user_initials(cntxt)
        self.assertEqual(chars, ' R', "should return 'blank-R'")
