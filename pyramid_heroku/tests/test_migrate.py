# -*- coding: utf-8 -*-
"""Tests for Heroku migrate script."""

from mock import call

import mock
import responses
import unittest


class TestHerokuMigrate(unittest.TestCase):

    def setUp(self):
        from pyramid_heroku.migrate import Heroku
        self.Heroku = Heroku

    def test_default_values(self):
        from pyramid_heroku.migrate import main

        def assert_args(args, called_with):
            with mock.patch('sys.argv', ['migrate.py'] + args),\
                 mock.patch('pyramid_heroku.migrate.Heroku') as heroku:
                main()
            heroku.assert_called_with(*called_with)

        # all default
        assert_args(
            ['my_test_app'],
            ['my_test_app', 'etc/production.ini', 'app:main'])

        # only app_section default
        assert_args(
            ['my_test_app', 'etc/develop.ini'],
            ['my_test_app', 'etc/develop.ini', 'app:main'])

        # all custom
        assert_args(
            ['my_test_app', 'etc/develop2.ini', 'app:main2'],
            ['my_test_app', 'etc/develop2.ini', 'app:main2'])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.print')
    def test_scale_down(self, out):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        responses.add(
            responses.GET,
            'https://api.heroku.com/apps/test/formation',  # noqa
            status=200,
            json=[{'type': 'web', 'quantity': 1}]
        )
        responses.add(
            responses.PATCH,
            'https://api.heroku.com/apps/test/formation',  # noqa
            status=200,
            json=[{'type': 'web', 'quantity': 0}]
        )
        h.scale_down()
        out.assert_has_calls([call('Scaled down to:'), call('web=0')])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.print')
    def test_scale_up(self, out):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        responses.add(
            responses.GET,
            'https://api.heroku.com/apps/test/formation',  # noqa
            status=200,
            json=[{'type': 'web', 'quantity': 1}]
        )
        responses.add(
            responses.PATCH,
            'https://api.heroku.com/apps/test/formation',  # noqa
            status=200,
            json=[{'type': 'web', 'quantity': 5}]
        )
        h.scale_up()
        out.assert_has_calls([call('Scaled up to:'), call('web=5')])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.print')
    def test_maintenance_on(self, out):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        responses.add(
            responses.PATCH,
            'https://api.heroku.com/apps/test',  # noqa
            status=200,
        )
        h.set_maintenance(True)
        out.assert_has_calls([call('Maintenance enabled')])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.print')
    def test_maintenance_off(self, out):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        responses.add(
            responses.PATCH,
            'https://api.heroku.com/apps/test',  # noqa
            status=200,
        )
        h.set_maintenance(False)
        out.assert_has_calls([call('Maintenance disabled')])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.subprocess')
    def test_needs_migrate(self, sub):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        sub.check_output.return_value = ''
        self.assertTrue(h.needs_migrate())
        sub.check_output.assert_called_with(
            ['bin/alembic', '-c', 'etc/production.ini',
             '-n', 'app:main', 'current']
        )

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.subprocess')
    def test_does_not_need_migrate(self, sub):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        sub.check_output.return_value = 'head'
        self.assertFalse(h.needs_migrate())
        sub.check_output.assert_called_with(
            ['bin/alembic', '-c', 'etc/production.ini',
             '-n', 'app:main', 'current']
        )

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.subprocess')
    def test_alembic(self, sub):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        sub.check_output.return_value = 'Migration done'
        self.assertEqual(h.alembic(), 'Migration done')
        sub.check_output.assert_called_with(
            ['bin/alembic', '-c', 'etc/production.ini', '-n', 'app:main',
             'upgrade', 'head']
        )

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.subprocess')
    @mock.patch('pyramid_heroku.migrate.print')
    @mock.patch('pyramid_heroku.migrate.sleep')
    def test_migrate_skip(self, sleep, out, sub):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        sub.check_output.return_value = 'head'
        h.migrate()
        sub.check_output.assert_called_with(
            ['bin/alembic', '-c', 'etc/production.ini',
             '-n', 'app:main', 'current']
        )
        out.assert_has_calls(
            [call('head'), call('Database migration is not needed')])

    @responses.activate
    @mock.patch('pyramid_heroku.migrate.subprocess')
    @mock.patch('pyramid_heroku.migrate.print')
    @mock.patch('pyramid_heroku.migrate.sleep')
    @mock.patch('pyramid_heroku.migrate.Session')
    def test_migrate(self, ses, sleep, out, sub):
        h = self.Heroku('test', 'etc/production.ini', 'app:main')
        sub.check_output.return_value = ''
        h.migrate()
        sub.check_output.assert_called_with(
            ['bin/alembic', '-c', 'etc/production.ini', '-n', 'app:main',
             'upgrade', 'head']
        )
