"""Tests for RequestIDLogger tween"""

from contextlib import contextmanager
from pyramid import request
from pyramid import testing

import unittest
from unittest import mock
import structlog
import sentry_sdk


class TestRequestIDLogger(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = request.Request({})

        self.handler = mock.Mock()
        self.registry = None

        self.request_id = "some-random-requestid"

        self.some_random_dsn = "https://some@random.dsn/12345"

    def tearDown(self):
        testing.tearDown()

    def test_request_id_in_sentry(self):
        sentry_sdk.init(self.some_random_dsn)
        from pyramid_heroku.request_id import RequestIDLogger

        self.request.headers["X-Request-ID"] = self.request_id
        RequestIDLogger(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(
            sentry_sdk.Hub.current._stack[-1][1]._tags,
            {"request_id": self.request_id}
        )

    def test_request_id_in_structlog(self):
        structlog.reset_defaults()
        from pyramid_heroku.request_id import RequestIDLogger

        context_class = structlog.get_config().get('context_class')
        self.assertEqual(context_class, dict)

        self.request.headers["X-Request-ID"] = self.request_id
        RequestIDLogger(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)

        context_class = structlog.get_config().get('context_class')
        self.assertEqual(
            context_class._tl.dict_, {"request_id": self.request_id}
        )

    def test_no_request_id_in_sentry(self):
        sentry_sdk.init(self.some_random_dsn)
        from pyramid_heroku.request_id import RequestIDLogger

        RequestIDLogger(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(sentry_sdk.Hub.current._stack[-1][1]._tags, {})

    def test_no_request_id_in_structlog(self):
        structlog.reset_defaults()
        from pyramid_heroku.request_id import RequestIDLogger

        context_class = structlog.get_config().get('context_class')
        self.assertEqual(context_class, dict)

        RequestIDLogger(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)

        context_class = structlog.get_config().get('context_class')
        self.assertEqual(context_class, dict)
