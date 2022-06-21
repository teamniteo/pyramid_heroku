"""Tests for ClientAddr tween."""

from pyramid import request
from pyramid import testing
from zope.testing.loggingsupport import InstalledHandler

import logging
import mock
import responses
import structlog
import unittest

tweens_handler = InstalledHandler("pyramid_heroku.client_addr")


class TestClientAddrTween(unittest.TestCase):
    def wrap_logger(self, _, __, event_dict):
        """Have structlog output to the standard logger, so that tweens_handler can intercept its messages."""
        wrapped_logger = logging.getLogger("pyramid_heroku.client_addr")
        wrapped_logger.info(event_dict["event"])
        return event_dict["event"]

    def setUp(self):
        tweens_handler.clear()
        self.config = testing.setUp()
        self.request = request.Request({})

        self.handler = mock.Mock()
        self.registry = mock.Mock()
        self.registry.settings = {}

        self.responses = responses.RequestsMock()
        self.responses.start()
        self.responses.add(
            responses.GET,
            "https://www.cloudflare.com/ips-v4",
            status=200,
            body="8.8.8.0/24\n9.9.9.0/24",
        )
        self.responses.add(
            responses.GET,
            "https://www.cloudflare.com/ips-v6",
            status=200,
            body="2400:cb00::/32\n2606:4700::/32",
        )

        structlog.configure(processors=[self.wrap_logger], context_class=dict)

    def tearDown(self):
        self.responses.stop()
        self.responses.reset()
        tweens_handler.clear()
        testing.tearDown()

    def test_direct_access(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "1.2.3.4"
        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_proxy_access(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = "6.6.6.6,1.2.3.4"

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_spaces(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = " 6.6.6.6, 1.2.3.4 "

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_cloudflare_ip_ignored(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = "6.6.6.6, 1.2.3.4, 9.9.9.9"

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_cloudflare_ipv6_ignored(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = (
            "2600:cb00:0000:0000:0000:0000:0000:0001, "
            "2500:cb00:0000:0000:0000:0000:0000:0001, "
            "2400:cb00:0000:0000:0000:0000:0000:0001"
        )

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(
            self.request.client_addr, "2500:cb00:0000:0000:0000:0000:0000:0001"
        )

    def test_invalid_ips(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = "1.2.3.4, invalid_ip not_ip"

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_cloudflare_ipv4_6_ignored(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers[
            "X-Forwarded-For"
        ] = "1.2.3.4, 9.9.9.9, 2400:cb00:0000:0000:0000:0000:0000:0001"

        ClientAddr(self.handler, self.registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "1.2.3.4")

    def test_cloudflare_ip_list_get_error(self):
        from pyramid_heroku.client_addr import ClientAddr

        self.responses.reset()
        self.responses.add(
            responses.GET, "https://www.cloudflare.com/ips-v4", status=501, body="error"
        )
        self.responses.add(
            responses.GET, "https://www.cloudflare.com/ips-v6", status=501, body="error"
        )

        self.request.environ["REMOTE_ADDR"] = "127.0.0.1"  # load balancer
        self.request.headers["X-Forwarded-For"] = " 6.6.6.6, 1.2.3.4, 9.9.9.9"

        registry = mock.Mock()
        registry.settings = {}
        ClientAddr(self.handler, registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "9.9.9.9")

        self.assertEqual(len(tweens_handler.records), 2)
        self.assertEqual(
            "Failed getting a list of IPs from https://www.cloudflare.com/ips-v4",
            tweens_handler.records[0].msg,
        )
        self.assertEqual(
            "Failed getting a list of IPs from https://www.cloudflare.com/ips-v6",
            tweens_handler.records[1].msg,
        )

        # structlog logging
        tweens_handler.clear()
        self.responses.reset()
        self.responses.add(
            responses.GET,
            "https://www.cloudflare.com/ips-v4",  # noqa
            status=501,
            body="error",
        )
        self.responses.add(
            responses.GET, "https://www.cloudflare.com/ips-v6", status=501, body="error"
        )

        registry.settings = {"pyramid_heroku.structlog": True}
        ClientAddr(self.handler, registry)(self.request)
        self.handler.assert_called_with(self.request)
        self.assertEqual(self.request.client_addr, "9.9.9.9")

        self.assertEqual(len(tweens_handler.records), 2)
        self.assertEqual(
            "Failed getting a list of IPs from https://www.cloudflare.com/ips-v4",
            tweens_handler.records[0].msg,
        )
        self.assertEqual(
            "Failed getting a list of IPs from https://www.cloudflare.com/ips-v6",
            tweens_handler.records[1].msg,
        )
