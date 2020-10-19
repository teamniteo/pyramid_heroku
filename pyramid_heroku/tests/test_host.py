"""Tests for Host tween."""

from pyramid import request
from pyramid import testing

import mock
import unittest


class TestHostTween(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = request.Request({})

        self.handler = mock.Mock()
        self.registry = None

    def tearDown(self):
        testing.tearDown()

    def test_direct_access(self):
        from pyramid_heroku.host import Host

        self.request.environ["HTTP_HOST"] = "foo.com"
        Host(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.host, "foo.com")

    def test_proxy_access(self):
        from pyramid_heroku.host import Host

        self.request.environ["HTTP_HOST"] = "foo.com"
        self.request.headers["X-Forwarded-Host"] = "bar.com"

        Host(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.host, "bar.com")
