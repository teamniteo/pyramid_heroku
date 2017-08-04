# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from future.utils import iteritems

from requests import Session
from time import sleep

import argparse
import os
import shlex
import subprocess
import sys


class Heroku(object):

    api_endpoint = 'https://api.heroku.com'

    def __init__(self, app_name, ini_file, app_section):
        # type: (str, str)-> ()
        """
        :param app_name: Name of Heroku app or id.
        :param app_section: Config section of app that needs migration.
        """
        self._formation = None
        self.app_name = app_name
        self.ini_file = ini_file
        self.app_section = app_section

        headers = {
            'Authorization': 'Bearer {0.auth_key}'.format(self),
            'Accept': 'application/vnd.heroku+json; version=3',
            'Content-Type': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(headers)

    @property
    def auth_key(self):
        # type: () -> str
        """Heroku API secret.

        https://devcenter.heroku.com/articles/platform-api-quickstart#authentication.
        """
        return os.environ.get('MIGRATE_API_SECRET_HEROKU')

    def scale_down(self):
        """Scale all app workers to 0."""
        updates = [dict(type=t, quantity=0) for t in self.formation.keys()]
        res = self.session.patch(
            '{0.api_endpoint}/apps/{0.app_name}/formation'.format(self),
            json=dict(updates=updates),
        )
        self.parse_response(res)
        print('Scaled down to:')
        for x in res.json():
            print('{}={}'.format(x['type'], x['quantity']))

    def scale_up(self):
        """Scale app back to initial state."""
        updates = [dict(type=t, quantity=s) for t, s in
                   iteritems(self.formation)]
        res = self.session.patch(
            '{0.api_endpoint}/apps/{0.app_name}/formation'.format(self),
            json=dict(updates=updates),
        )
        self.parse_response(res)
        print('Scaled up to:')
        for x in res.json():
            print('{}={}'.format(x['type'], x['quantity']))

    @property
    def formation(self):
        """Get current app status and configuration.

        :return: Heroku app status as dict.
        """
        if not self._formation:
            res = self.session.get(
                '{0.api_endpoint}/apps/{0.app_name}/formation'.format(self)
            )
            self.parse_response(res)
            self._formation = {x['type']: x['quantity'] for x in res.json()}
        return self._formation

    def shell(self, cmd):
        # type: (str) -> str
        """
        Run shell command.

        :param cmd: shell command to run
        :return: stdout of command
        """
        return subprocess.check_output(shlex.split(cmd))

    def needs_migrate(self):
        """
        Checks current status of alembic branches.

        :return: True if current alembic branch is not up to date.
        """
        cmd = self.shell('bin/alembic -c {0.ini_file}'
                         ' -n {0.app_section} current'.format(self))
        print(cmd)
        return 'head' not in cmd

    def alembic(self):
        """
        Run alembic migrations.

        :return: alembic stdout
        """
        return self.shell('bin/alembic -c {0.ini_file}'
                          ' -n {0.app_section} upgrade head'.format(self))

    def set_maintenance(self, state):
        # type: (bool) -> ()
        res = self.session.patch(
            '{0.api_endpoint}/apps/{0.app_name}'.format(self),
            json=dict(maintenance=state),
        )
        if self.parse_response(res):
            print('Maintenance {}'.format('enabled' if state else 'disabled'))

    def parse_response(self, res):
        # type: (requests.Response) -> bool
        """
        Parses Heroku API response.

        :param res: requests object
        :return: true if request succeeded
        """
        if res.status_code != 200:
            print(res.json())
        res.raise_for_status()
        return True

    def migrate(self):
        """Run database migration if needed."""
        print(self.app_name)
        print(self.app_section)
        print(self.ini_file)

        if self.needs_migrate():
            self.set_maintenance(True)
            self.scale_down()
            sleep(30)
            print(self.alembic())
            self.scale_up()
            sleep(30)
            self.set_maintenance(False)
        else:
            print('Database migration is not needed')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=(
            'usage: migrate.py [-h] app_name [ini_file] [app_section]'
            '\nexample: python -m pyramid_heroku.migrate my_app etc/production.ini app:main'),
    )
    parser.add_argument('app_name', help='Heroku app name')
    parser.add_argument(
        'ini_file',
        nargs='?',
        default='etc/production.ini',
        help='Path to Pyramid configuration file ')
    parser.add_argument(
        'app_section',
        nargs='?',
        default='app:main',
        help='App section name in ini configuration file')

    options = parser.parse_args()

    Heroku(options.app_name, options.ini_file, options.app_section).migrate()


if __name__ == '__main__':
    main()
