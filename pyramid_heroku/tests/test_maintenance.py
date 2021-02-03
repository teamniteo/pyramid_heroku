"""Tests for Heroku maintenance script."""


from pyramid_heroku.maintenance import main

import mock
import pytest
import responses
import unittest


class TestHerokuMaintenance(unittest.TestCase):
    def setUp(self):
        from pyramid_heroku.heroku import Heroku

        self.Heroku = Heroku

    def test_default_values(self):
        from pyramid_heroku.maintenance import main

        def assert_args(args, called_with):
            with mock.patch("sys.argv", ["migrate.py"] + args), mock.patch(
                "pyramid_heroku.maintenance.Heroku"
            ) as heroku:
                main()
            heroku.assert_called_with(*called_with)

        # all default
        assert_args(["on", "my_test_app"], ["my_test_app", "etc/production.ini"])

        # all custom
        assert_args(
            ["on", "my_test_app", "etc/develop2.ini"],
            ["my_test_app", "etc/develop2.ini"],
        )

    @mock.patch("pyramid_heroku.maintenance.Heroku")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_migrate_on(self, sess, Heroku):

        with mock.patch("sys.argv", ["maintenance.py", "on", "my_app"]):
            main()

        Heroku().set_maintenance.assert_called_once_with(True)

    @mock.patch("pyramid_heroku.maintenance.Heroku")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_migrate_off(self, sess, Heroku):

        with mock.patch("sys.argv", ["maintenance.py", "off", "my_app"]):
            main()

        Heroku().set_maintenance.assert_called_once_with(False)

    @mock.patch("pyramid_heroku.subprocess")
    @mock.patch("pyramid_heroku.print")
    @mock.patch("pyramid_heroku.heroku.Session")
    @responses.activate
    def test_maintenance_non_zero(self, ses, out, sub):
        h = self.Heroku("test", "etc/production.ini")
        p = mock.Mock()
        p.stdout = b"foo"
        p.stderr = b"bar"
        p.check_returncode.side_effect = Exception
        sub.run.return_value = p

        with pytest.raises(Exception):
            main(h)

        assert not out.called
