"""Tests for Heroku migrate script."""

from mock import call

import mock
import pytest
import responses
import unittest


class TestHerokuMigrate(unittest.TestCase):
    def setUp(self):
        from pyramid_heroku.migrate import Heroku

        self.Heroku = Heroku

    def test_default_values(self):
        from pyramid_heroku.migrate import main

        def assert_args(args, called_with):
            with mock.patch("sys.argv", ["migrate.py"] + args), mock.patch(
                "pyramid_heroku.migrate.Heroku"
            ) as heroku:
                main()
            heroku.assert_called_with(*called_with)

        # all default
        assert_args(["my_test_app"], ["my_test_app", "etc/production.ini"])

        # all custom
        assert_args(
            ["my_test_app", "etc/develop2.ini"], ["my_test_app", "etc/develop2.ini"]
        )

    @mock.patch("pyramid_heroku.migrate.print")
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

    @mock.patch("pyramid_heroku.migrate.print")
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

    @mock.patch("pyramid_heroku.migrate.print")
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

    @mock.patch("pyramid_heroku.migrate.print")
    @responses.activate
    def test_maintenance_on(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.PATCH, "https://api.heroku.com/apps/test", status=200  # noqa
        )
        h.set_maintenance(True)
        out.assert_has_calls([call("Maintenance enabled")])

    @mock.patch("pyramid_heroku.migrate.print")
    @responses.activate
    def test_maintenance_off(self, out):
        h = self.Heroku("test", "etc/production.ini")
        responses.add(
            responses.PATCH, "https://api.heroku.com/apps/test", status=200  # noqa
        )
        h.set_maintenance(False)
        out.assert_has_calls([call("Maintenance disabled")])

    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.Heroku.parse_response", return_value=False)
    def test_set_maintanence_fail(self, pr, out):
        """Test that set_maintenance() doesn't print the maintenance state if the call to it failed."""
        h = self.Heroku("test", "etc/production.ini")
        h.set_maintenance(True)
        out.assert_not_called()

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @responses.activate
    def test_needs_migrate(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        sub.run.stdout.return_value = b""
        self.assertTrue(h.needs_migrate())
        sub.run.assert_called_with(
            [
                "alembic",
                "-c",
                "etc/alembic.ini",
                "-x",
                "ini=etc/production.ini",
                "current",
            ],
            stdout=mock.ANY,
            stderr=mock.ANY,
        )

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @responses.activate
    def test_does_not_need_migrate(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        self.assertFalse(h.needs_migrate())
        sub.run.assert_called_with(
            [
                "alembic",
                "-c",
                "etc/alembic.ini",
                "-x",
                "ini=etc/production.ini",
                "current",
            ],
            stdout=mock.ANY,
            stderr=mock.ANY,
        )

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @responses.activate
    def test_alembic(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        h.alembic()
        # TODO: print(migration done)
        sub.run.assert_called_with(
            [
                "alembic",
                "-c",
                "etc/alembic.ini",
                "-x",
                "ini=etc/production.ini",
                "upgrade",
                "head",
            ],
            stdout=mock.ANY,
            stderr=mock.ANY,
        )

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @responses.activate
    def test_migrate_skip(self, sleep, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        h.migrate()
        sub.run.assert_called_with(
            [
                "alembic",
                "-c",
                "etc/alembic.ini",
                "-x",
                "ini=etc/production.ini",
                "current",
            ],
            stdout=mock.ANY,
            stderr=mock.ANY,
        )
        out.assert_has_calls(
            [call("head"), call("Database migration is not needed")], any_order=True
        )

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @mock.patch("pyramid_heroku.migrate.Session")
    @responses.activate
    def test_migrate(self, ses, sleep, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        h.migrate()
        sub.run.assert_called_with(
            [
                "alembic",
                "-c",
                "etc/alembic.ini",
                "-x",
                "ini=etc/production.ini",
                "upgrade",
                "head",
            ],
            stdout=mock.ANY,
            stderr=mock.ANY,
        )

    @mock.patch("pyramid_heroku.migrate.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @mock.patch("pyramid_heroku.migrate.Session")
    @responses.activate
    def test_migrate_non_zero(self, ses, sleep, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"foo"
        p.stderr = b"bar"
        p.check_returncode.side_effect = Exception
        sub.run.return_value = p

        with pytest.raises(Exception):
            h.migrate()

        out.assert_has_calls([call("foo"), call("bar", file=mock.ANY)], any_order=True)
