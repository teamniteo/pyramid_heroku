"""Enable or disable Heroku app maintenance mode."""

from enum import Enum
from pyramid_heroku.heroku import Heroku

import argparse


class Mode(Enum):
    """Heroku maintenance modes."""

    on = "ON"
    off = "OFF"


def main() -> None:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        usage=(
            "usage: maintenance.py [-h] [app_name] [ini_file] [on|off]"
            "\nexample: python -m pyramid_heroku.maintenance on my_app etc/production.ini"
        ),
    )
    parser.add_argument("mode", choices=[x.name for x in Mode], help="Maintenance mode")
    parser.add_argument("app_name", help="Heroku app name")
    parser.add_argument(
        "ini_file",
        nargs="?",
        default="etc/production.ini",
        help="Path to Pyramid configuration file ",
    )

    options = parser.parse_args()

    h = Heroku(options.app_name, options.ini_file)

    if Mode[options.mode] == Mode.on:
        h.set_maintenance(True)
    else:
        h.set_maintenance(False)


if __name__ == "__main__":
    main()
