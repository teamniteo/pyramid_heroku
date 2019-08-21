"""Graceful DB migrations."""

from requests import Session, Response
from time import sleep
from typing import Optional

import argparse
import os
import shlex
import subprocess
import sys


class Heroku(object):

    api_endpoint = "https://api.heroku.com"

    def __init__(self, app_name: str, ini_file: str) -> None:
        """
        :param app_name: Name of Heroku app or id.
        :param ini_file: development.ini or production.ini filename.
        """
        self._formation = None
        self.app_name = app_name
        self.ini_file = ini_file

        headers = {
            "Authorization": f"Bearer {self.auth_key}",
            "Accept": "application/vnd.heroku+json; version=3",
            "Content-Type": "application/json",
        }
        self.session = Session()
        self.session.headers.update(headers)

    @property
    def auth_key(self) -> Optional[str]:
        """Heroku API secret.

        https://devcenter.heroku.com/articles/platform-api-quickstart#authentication.
        """
        return os.environ.get("MIGRATE_API_SECRET_HEROKU")

    def scale_down(self):
        """Scale all app workers to 0."""
        updates = [dict(type=t, quantity=0) for t in self.formation.keys()]
        res = self.session.patch(
            f"{self.api_endpoint}/apps/{self.app_name}/formation",
            json=dict(updates=updates),
        )
        self.parse_response(res)
        print("Scaled down to:")
        for x in res.json():
            print(f'{x["type"]}={x["quantity"]}')

    def scale_up(self):
        """Scale app back to initial state."""
        updates = [dict(type=t, quantity=s) for t, s in self.formation.items()]
        res = self.session.patch(
            f"{self.api_endpoint}/apps/{self.app_name}/formation",
            json=dict(updates=updates),
        )
        self.parse_response(res)
        print("Scaled up to:")
        for x in res.json():
            print(f'{x["type"]}={x["quantity"]}')

    @property
    def formation(self):
        """Get current app status and configuration.

        :return: Heroku app status as dict.
        """
        if not self._formation:
            res = self.session.get(
                f"{self.api_endpoint}/apps/{self.app_name}/formation"
            )
            self.parse_response(res)
            self._formation = {x["type"]: x["quantity"] for x in res.json()}
        return self._formation

    def shell(self, cmd: str) -> str:
        """
        Run shell command.

        :param cmd: shell command to run
        :return: stdout of command
        """

        p = subprocess.run(
            shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(p.stdout.decode())
        print(p.stderr.decode(), file=sys.stderr)
        p.check_returncode()
        return p.stdout.decode()

    def needs_migrate(self):
        """
        Checks current status of alembic branches.

        :return: True if current alembic branch is not up to date.
        """
        cmd = self.shell(f"alembic -c etc/alembic.ini -x ini={self.ini_file} current")
        return "head" not in cmd

    def alembic(self):
        """
        Run alembic migrations.
        """
        self.shell(f"alembic -c etc/alembic.ini -x ini={self.ini_file} upgrade head")

    def set_maintenance(self, state: bool) -> None:
        res = self.session.patch(
            f"{self.api_endpoint}/apps/{self.app_name}", json=dict(maintenance=state)
        )
        if self.parse_response(res):
            print("Maintenance {}".format("enabled" if state else "disabled"))

    def parse_response(self, res: Response) -> Optional[bool]:
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
        print(self.ini_file)

        if self.needs_migrate():
            self.set_maintenance(True)
            self.scale_down()
            sleep(30)
            self.alembic()
            self.scale_up()
            sleep(30)
            self.set_maintenance(False)
        else:
            print("Database migration is not needed")


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=(
            "usage: migrate.py [-h] [app_name] [ini_file]"
            "\nexample: python -m pyramid_heroku.migrate my_app etc/production.ini"
        ),
    )
    parser.add_argument("app_name", help="Heroku app name")
    parser.add_argument(
        "ini_file",
        nargs="?",
        default="etc/production.ini",
        help="Path to Pyramid configuration file ",
    )

    options = parser.parse_args()

    Heroku(options.app_name, options.ini_file).migrate()


if __name__ == "__main__":
    main()
