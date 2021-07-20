import json
from datetime import date

from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import path

from accounts.models import User
from ..api import Preparer, ApiError, ApiBase


class TestPreparer(TestCase):

    def test_prepare(self):
        d = {'username': 'username', 'email': 'email'}

        prep = Preparer(None)
        rc = prep.prepare(d)
        self.assertDictEqual(rc, d, "should return data unchanged")

        usr_dict = {'username': 'dorothy', 'email': 'dot@kansas.gov'}
        usr = User(username=usr_dict['username'],
                   email=usr_dict['email'],
                   password='rubySlippers')
        prep = Preparer(d)
        rc = prep.prepare(usr)
        self.assertDictEqual(rc, usr_dict)

    def test_extract_data(self):

        class SimpleObject(object):
            count = 1
            result = object()

            def get_json_url(self):
                return '/base/0'

        class TestObject(object):
            options = {'first': 1, 'last': 99}
            child = SimpleObject()

            def say(self):
                return 'testing....'

        to = TestObject()
        prep = Preparer(None)

        rc = prep.extract_data('.', 'text')
        self.assertEquals(rc, 'text', "should return data unchanged")
        rc = prep.extract_data('count', None)
        self.assertIsNone(rc, "should handle null case")
        rc = prep.extract_data('say', to)
        self.assertEquals(rc, to.say(), "should return function result")
        rc = prep.extract_data('child', to)
        self.assertEquals(rc, to.child.get_json_url(),
                          "should urlize value")
        # test parsing of dotted names
        rc = prep.extract_data('options.last', to)
        self.assertEquals(rc, 99, "should handle dictionary entries")
        rc = prep.extract_data('child.result.__class__', to)
        self.assertIsInstance(rc, object, "should handle multiple dot-levels")


class TestApiError(TestCase):

    def err_func(self, msg=None):
        raise ApiError(msg)

    def test_empty_message(self):
        with self.assertRaisesMessage(ApiError, 'Api Error') as ctx:
            self.err_func()

    def test_with_message(self):
        with self.assertRaisesMessage(ApiError, 'custom message') as ctx:
            self.err_func('custom message')


class TestApiBase(TestCase):

    def test_init(self):
        api = ApiBase()
        self.assertIsInstance(api, ApiBase)

    def test_classmethods(self):
        name = ApiBase.build_url_name('list')
        self.assertEquals(name, 'api_base_list')

        pathlist = ['base', 'base/<int:pk>']
        urls = ApiBase.urls()
        paths = [x.pattern._route for x in urls]
        for path in paths:
            self.assertIn(path, pathlist, "{} should be a route".format(path))

    def test_handler(self):

        rf = RequestFactory()
        func = ApiBase.as_list()

        resp = func(rf.options('check'))
        self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
        d = json.loads(resp.content)
        self.assertIn('error', d, "should contain error message")
        self.assertEquals(d['error'], "The specified HTTP method OPTIONS is not implemented.")

        with self.settings(DEBUG=True):
            resp = func(rf.post({}))
            self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
            d = json.loads(resp.content)
            self.assertIn('error', d, "should contain error message")
            self.assertEquals(d['error'], "Unauthorized")
            self.assertIn('traceback', d, "should contain traceback")

        resp = func(rf.get('base'))
        self.assertIsInstance(resp, JsonResponse, "should return JsonResponse")
        d = json.loads(resp.content)
        self.assertIn('error', d, "should contain error message")
        self.assertEquals(d['error'], 'The "list" method is not implemented.')
