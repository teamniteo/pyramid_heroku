# -*- coding: utf-8 -*-
"""Tests for ClientAddr tween."""

from __future__ import unicode_literals
from pyramid import request
from pyramid import testing

import mock
import unittest


class TestClientAddrTween(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.request = request.Request({})

        self.handler = mock.Mock()
        self.registry = None

    def tearDown(self):
        testing.tearDown()

    def test_direct_access(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ['REMOTE_ADDR'] = '1.2.3.4'
        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, '1.2.3.4')

    def test_proxy_access(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ['REMOTE_ADDR'] = '127.0.0.1'  # load balancer
        self.request.headers['X-Forwarded-For'] = '6.6.6.6,1.2.3.4'

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, '1.2.3.4')

    def test_spaces(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ['REMOTE_ADDR'] = '127.0.0.1'  # load balancer
        self.request.headers['X-Forwarded-For'] = ' 6.6.6.6, 1.2.3.4 '

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, '1.2.3.4')
