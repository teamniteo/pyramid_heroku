"""Tests for Heroku migrate script."""

from mock import call
from pyramid_heroku.migrate import alembic
from pyramid_heroku.migrate import migrate
from pyramid_heroku.migrate import needs_migrate

import mock
import pytest
import responses
import unittest


class TestHerokuMigrate(unittest.TestCase):
    def setUp(self):
        from pyramid_heroku.heroku import Heroku

        self.Heroku = Heroku

    def test_default_values(self):
        from pyramid_heroku.migrate import main

        def assert_args(args, called_with):
            with mock.patch("sys.argv", ["migrate.py"] + args), mock.patch(
                "pyramid_heroku.migrate.Heroku"
            ) as heroku, mock.patch("pyramid_heroku.migrate.migrate"):
                main()
            heroku.assert_called_with(*called_with)

        # all default
        assert_args(["my_test_app"], ["my_test_app", "etc/production.ini"])

        # all custom
        assert_args(
            ["my_test_app", "etc/develop2.ini"], ["my_test_app", "etc/develop2.ini"]
        )

    @mock.patch("pyramid_heroku.subprocess")
    @responses.activate
    def test_needs_migrate(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        sub.run.stdout.return_value = b""
        self.assertTrue(needs_migrate(h))
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

    @mock.patch("pyramid_heroku.subprocess")
    @responses.activate
    def test_does_not_need_migrate(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        self.assertFalse(needs_migrate(h))
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

    @mock.patch("pyramid_heroku.subprocess")
    @responses.activate
    def test_alembic(self, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        alembic(h)
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

    @mock.patch("pyramid_heroku.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @responses.activate
    def test_migrate_skip(self, sleep, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"head"
        sub.run.return_value = p
        migrate(h)
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
        out.assert_has_calls([call("Database migration is not needed")], any_order=True)

    @mock.patch("pyramid_heroku.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_migrate_with_maintenance_mode(self, ses, sleep, out, sub):

        h = self.Heroku("test", "etc/production.ini")
        h.get_maintenance = mock.Mock(return_value=False)
        h.set_maintenance = mock.Mock()
        migrate(h)

        h.set_maintenance.assert_has_calls([call(True), call(False)])
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

    @mock.patch("pyramid_heroku.subprocess")
    @mock.patch("pyramid_heroku.migrate.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_migrate_skip_setting_maintenance_mode(self, ses, sleep, out, sub):

        h = self.Heroku("test", "etc/production.ini")
        h.get_maintenance = mock.Mock(return_value=True)
        h.set_maintenance = mock.Mock()
        migrate(h)

        assert not h.set_maintenance.called
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

    @mock.patch("pyramid_heroku.subprocess")
    @mock.patch("pyramid_heroku.print")
    @mock.patch("pyramid_heroku.migrate.sleep")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_migrate_non_zero(self, ses, sleep, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"foo"
        p.stderr = b"bar"
        p.check_returncode.side_effect = Exception
        sub.run.return_value = p

        with pytest.raises(Exception):
            migrate(h)

        out.assert_has_calls([call("foo"), call("bar", file=mock.ANY)], any_order=True)
