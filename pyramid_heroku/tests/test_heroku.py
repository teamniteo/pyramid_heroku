"""Tests for Heroku API client."""

from mock import call

import json
import mock
import responses
import unittest


class TestHeroku(unittest.TestCase):
    def setUp(self):
        from pyramid_heroku.heroku import Heroku

        self.Heroku = Heroku

    @mock.patch("pyramid_heroku.heroku.print")
    @responses.activate
    def test_default_formation(self, out):
        h = self.Heroku("test", "etc/production.ini")
        h._formation = {"type": "web", "quantity": 8999}
        responses.add(
            responses.PATCH,
            "https://api.heroku.com/apps/test/formation",  # noqa
            status=200,
            json=[{"type": "web", "quantity": 9001}],
        )
        h.scale_up()
        out.assert_has_calls([call("Scaled up to:"), call("web=9001")])

    @mock.patch("pyramid_heroku.heroku.print")
    @responses.activate
    def test_scale_down(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.GET,
            "https://api.heroku.com/apps/test/formation",  # noqa
            status=200,
            json=[{"type": "web", "quantity": 1}],
        )
        responses.add(
            responses.PATCH,
            "https://api.heroku.com/apps/test/formation",  # noqa
            status=200,
            json=[{"type": "web", "quantity": 0}],
        )
        h.scale_down()
        out.assert_has_calls([call("Scaled down to:"), call("web=0")])

    @mock.patch("pyramid_heroku.heroku.print")
    @responses.activate
    def test_scale_up(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.GET,
            "https://api.heroku.com/apps/test/formation",  # noqa
            status=200,
            json=[{"type": "web", "quantity": 1}],
        )
        responses.add(
            responses.PATCH,
            "https://api.heroku.com/apps/test/formation",  # noqa
            status=200,
            json=[{"type": "web", "quantity": 5}],
        )
        h.scale_up()
        out.assert_has_calls([call("Scaled up to:"), call("web=5")])

    @responses.activate
    def test_get_maintenance(self):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(  # noqa
            responses.GET,
            "https://api.heroku.com/apps/test",
            status=200,
            body=json.dumps({"maintenance": True}),
        )
        assert h.get_maintenance()

    @mock.patch("pyramid_heroku.heroku.print")
    @responses.activate
    def test_maintenance_on(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.PATCH, "https://api.heroku.com/apps/test", status=200  # noqa
        )
        h.set_maintenance(True)
        out.assert_has_calls([call("Maintenance enabled")])

    @mock.patch("pyramid_heroku.heroku.print")
    @responses.activate
    def test_maintenance_off(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.PATCH, "https://api.heroku.com/apps/test", status=200  # noqa
        )
        h.set_maintenance(False)
        out.assert_has_calls([call("Maintenance disabled")])

    @mock.patch("pyramid_heroku.heroku.print")
    @mock.patch("pyramid_heroku.heroku.Heroku.parse_response", return_value=False)
    def test_set_maintanence_fail(self, pr, out):
        """Test that set_maintenance() doesn't print the maintenance state if the call to it failed."""
        h = self.Heroku("test", "etc/production.ini")
        h.set_maintenance(True)
        out.assert_not_called()
