"""Tests for HerokuappAccess tween."""

from pyramid import testing
from zope.testing.loggingsupport import InstalledHandler

import logging
import mock
import os
import structlog
import unittest

tweens_handler = InstalledHandler("pyramid_heroku.herokuapp_access")


class TestHerokuappAccessTween(unittest.TestCase):
    def wrap_logger(self, _, __, event_dict):
        """Have structlog output to the standard logger, so that tweens_handler can intercept its messages."""
        wrapped_logger = logging.getLogger("pyramid_heroku.herokuapp_access")
        wrapped_logger.info(event_dict["event"])
        return event_dict["event"]

    def setUp(self):
        tweens_handler.clear()
        self.config = testing.setUp()
        self.handler = mock.Mock()
        self.request = testing.DummyRequest()
        self.request.registry.settings = {
            "pyramid_heroku.herokuapp_allowlist": "\n1.2.3.4\n5.6.7.8",
            "pyramid_heroku.structlog": 1,
        }
        structlog.configure(processors=[self.wrap_logger], context_class=dict)

    def tearDown(self):
        tweens_handler.clear()
        testing.tearDown()

    def test_allowlisted_ip(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "1.2.3.4"
        self.request.headers = {"Host": "foo.herokuapp.com"}

        HerokuappAccess(self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)

    def test_non_allowlisted_ip(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {"Host": "foo.herokuapp.com"}

        # structlog version
        # wrap structlog around a regular logger so that zope's logging support
        # still gets the logged messages
        response = HerokuappAccess(self.handler, self.request.registry)(self.request)
        assert not self.handler.called, "handler should not be called"
        self.assertEqual(len(tweens_handler.records), 1)
        self.assertEqual(
            "Herokuapp access denied", tweens_handler.records[0].msg  # noqa
        )
        self.assertEqual(response.status_code, 403)

        # standard logging version
        self.request.registry.settings["pyramid_heroku.structlog"] = False
        tweens_handler.clear()
        response = HerokuappAccess(self.handler, self.request.registry)(self.request)
        assert not self.handler.called, "handler should not be called"
        self.assertEqual(len(tweens_handler.records), 1)
        self.assertEqual(
            "Denied Herokuapp access for Host foo.herokuapp.com and IP 6.6.6.6",
            tweens_handler.records[0].msg,
        )
        self.assertEqual(response.status_code, 403)

    def test_other_hostname(self):
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {"Host": "foo.bar.com"}

        HerokuappAccess(self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)

    def test_herokuapp_allowlist_not_set(self):
        "Even if allowlist is not set, the protection should still work."
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {"Host": "foo.herokuapp.com"}
        self.request.registry.settings = {}

        HerokuappAccess(self.handler, self.request.registry)(self.request)
        assert not self.handler.called, "handler should not be called"

    def test_herokuapp_allowlist_empty(self):
        "Even if allowlist is empty, the protection should still work."
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {"Host": "foo.herokuapp.com"}
        self.request.registry.settings = {"pyramid_heroku.herokuapp_allowlist": ""}

        HerokuappAccess(self.handler, self.request.registry)(self.request)
        assert not self.handler.called, "handler should not be called"

    @mock.patch.dict(os.environ, {"HEROKUAPP_ACCESS_BYPASS": "foo"})
    def test_herokuapp_access_bypass(self):
        "The IP check can be bypassed by setting a correct header."
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {
            "Host": "foo.herokuapp.com",
            "User-Agent": "foo",
        }

        # structlog version
        HerokuappAccess(self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(len(tweens_handler.records), 1)
        self.assertEqual("Herokuapp access bypassed", tweens_handler.records[0].msg)

        # standard logging version
        self.request.registry.settings["pyramid_heroku.structlog"] = False
        tweens_handler.clear()
        HerokuappAccess(self.handler, self.request.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(len(tweens_handler.records), 1)
        self.assertEqual(
            "Herokuapp access bypassed by 6.6.6.6",
            tweens_handler.records[0].msg,
        )

    @mock.patch.dict(os.environ, {"HEROKUAPP_ACCESS_BYPASS": "foo"})
    def test_herokuapp_access_bypass_invalid(self):
        "Invalid bypass code is rejected."
        from pyramid_heroku.herokuapp_access import HerokuappAccess

        self.request.client_addr = "6.6.6.6"
        self.request.headers = {
            "Host": "foo.herokuapp.com",
            "User-Agent": "bar",
        }
        self.request.registry.settings = {}

        HerokuappAccess(self.handler, self.request.registry)(self.request)
        assert not self.handler.called, "handler should not be called"
