# -*- coding: utf-8 -*-
"""Tests for HerokuappAccess tween."""

from __future__ import unicode_literals
from pyramid import testing
from zope.testing.loggingsupport import InstalledHandler

import mock
import unittest
import six

tweens_handler = InstalledHandler('pyramid_heroku.herokuapp_access')


class TestHerokuappAccessTween(unittest.TestCase):

    def setUp(self):
        tweens_handler.clear()
        self.config = testing.setUp()
        self.handler = mock.Mock()
        self.request = testing.DummyRequest()
        self.request.registry.settings = {
            'pyramid_heroku.herokuapp_whitelist': ['1.2.3.4', ]}

    def tearDown(self):
        tweens_handler.clear()
        testing.tearDown()

    def test_whitelisted_ip(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess
        self.request.client_addr = '1.2.3.4'
        self.request.headers = {
            'Host': 'foo.herokuapp.com',
        }

        HerokuappAccess(
            self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)

    def test_non_whitelisted_ip(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess
        self.request.client_addr = '6.6.6.6'
        self.request.headers = {
            'Host': 'foo.herokuapp.com',
        }

        # !!!: By default, you won't get any logs from structlog.
        #      That is very error prone!
        import structlog
        # Setting logger_factory to be able to capture logs
        structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())

        response = HerokuappAccess(
            self.handler, self.request.registry)(self.request)
        assert not self.handler.called, 'handler should not be called'
        self.assertEqual(len(tweens_handler.records), 1)
        msg = (
            'Herokuapp access denied        host=foo.herokuapp.com user_ip=6.6.6.6'
            if six.PY3 else
            "Herokuapp access denied        host=u'foo.herokuapp.com' user_ip=u'6.6.6.6'")
        # import pdb; pdb.set_trace()
        self.assertTrue(msg in tweens_handler.records[0].msg)
        self.assertEqual(response.status_code, 403)

    def test_other_hostname(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess
        self.request.client_addr = '6.6.6.6'
        self.request.headers = {
            'Host': 'foo.bar.com',
        }

        HerokuappAccess(
            self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)

    def test_herokuapp_whitelist_not_set(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess
        self.request.client_addr = '6.6.6.6'
        self.request.headers = {
            'Host': 'foo.herokuapp.com',
        }
        self.request.registry.settings = {}

        HerokuappAccess(
            self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)

    def test_herokuapp_whitelist_empty(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess
        self.request.client_addr = '6.6.6.6'
        self.request.headers = {
            'Host': 'foo.herokuapp.com',
        }
        self.request.registry.settings = {
            'pyramid_heroku.herokuapp_whitelist': [], }

        HerokuappAccess(
            self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)
