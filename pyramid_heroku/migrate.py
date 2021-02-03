"""Graceful DB migrations."""


from pyramid_heroku import shell
from pyramid_heroku.heroku import Heroku
from time import sleep

import argparse


def needs_migrate(heroku: Heroku) -> bool:
    """
    Checks current status of alembic branches.

    :return: True if current alembic branch is not up to date.
    """
    cmd = shell(f"alembic -c etc/alembic.ini -x ini={heroku.ini_file} current")
    return "head" not in cmd


def alembic(heroku: Heroku) -> None:
    """
    Run alembic migrations.
    """
    shell(f"alembic -c etc/alembic.ini -x ini={heroku.ini_file} upgrade head")


def migrate(heroku: Heroku) -> None:
    """Run database migration if needed."""
    print(heroku.app_name)
    print(heroku.ini_file)

    if needs_migrate(heroku):
        was_in_maintenance = heroku.get_maintenance()
        if not was_in_maintenance:
            heroku.set_maintenance(True)
        heroku.scale_down()
        sleep(30)
        alembic(heroku)
        heroku.scale_up()
        sleep(30)
        if not was_in_maintenance:
            # Don't disable maintenance mode if it was enabled externally.
            heroku.set_maintenance(False)
    else:
        print("Database migration is not needed")


def main() -> None:
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

    migrate(Heroku(options.app_name, options.ini_file))


if __name__ == "__main__":
    main()
