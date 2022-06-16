pyramid_heroku
==============

Introduction
------------

pyramid_heroku is a collection of tweens and helpers to successfully run `Pyramid <http://www.trypyramid.com/>`_ on `Heroku <https://heroku.com/>`_

It provides the following:

* ``ClientAddr`` tween that sets real user's IP to ``request.client_addr``
* ``Host`` tween that sets `request.host` to proxied `X-Forwarded-Host` header (note: potential security risk)
* ``HerokuappAccess`` tween that denies access to your app's
  ``<app>.herokuapp.com`` domain for any non-whitelisted IPs.
* ``migrate.py`` script for automatically running alembic migrations on
  deploy.
* ``maintenance.py`` script for controlling Heroku maintenance mode.


Installation
------------

Just do

``pip install pyramid_heroku``

or

``easy_install pyramid_heroku``


Compatibility
-------------

pyramid_heroku runs with pyramid>=1.7 and python>=3.6.
Other versions might also work.


Documentation
-------------

Usage example for tweens::

    def main(global_config, **settings):$ cat .heroku/release.sh
        config = Configurator(settings=settings)
        config.include('pyramid_heroku.client_addr')
        config.include('pyramid_heroku.herokuapp_access')
        return config.make_wsgi_app()

The ``pyramid_heroku.herokuapp_access`` tween depends on
``pyramid_heroku.client_addr`` tween and it requires you to list whitelisted IPs
in the ``pyramid_heroku.herokuapp_whitelist`` setting.

The ``pyramid_heroku.client_addr`` tween sets request.client_addr to an IP we
can trust. It handles IP spoofing via ``X-Forwarded-For`` headers and
ignores Cloudflare's IPs when using Cloudflare reverse proxy.


Usage example for automatic alembic migration script::

    $ cat .heroku/release.sh
    #!/usr/bin/env bash

    set -e

    echo "Running migrations"
    python -m pyramid_heroku.migrate my_app etc/production.ini

    echo "DONE!"

For migration script to work, you need to set the ``MIGRATE_API_SECRET_HEROKU``
env var in Heroku. This allows the migration script to use the Heroku API.


Before running DB migration, the script will enable `Heroku maintenance mode <https://devcenter.heroku.com/articles/maintenance-mode>`_
if the app is not already in maintenance mode. After the migration, maintenance mode will
be disabled only if it was enabled by the migration script.

Maintenance mode can also be enabled/disabled using the ``pyramid_heroku.maintenance`` script.

Usage example for enabling the Heroku maintenance mode::

    python -m pyramid_heroku.maintenance on my_app etc/production.ini


If you use structlog, add the following configuration setting to your INI file to enable structlog-like logging::

    pyramid_heroku.structlog = true


See tests for more examples.



Releasing
---------

#. Update CHANGES.rst.
#. Update pyproject.toml version.
#. Run ``poetry check``.
#. Run ``poetry publish --build``.


We're hiring!
-------------

At Niteo we regularly contribute back to the Open Source community. If you do too, we'd like to invite you to `join our team
<https://niteo.co/careers/>`_!
