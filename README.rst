pyramid_heroku
================

------------
Introduction
------------

pyramid_heroku is a collection of tweens and helpers to successfully run `Pyramid <http://www.trypyramid.com/>`_ on `Heroku <https://heroku.com/>`_

It provides the following:

* ``ClientAddr`` tween that sets real user's IP to ``request.client_addr``
* ``HerokuappAccess`` tween that denies access to your app's
  ``<app>.herokuapp.com`` domain for any non-whitelisted IPs.
* ``migrate.py`` script for automatically running alembic migrations on
  deploy.

------------
Installation
------------

Just do

``pip install pyramid_heroku``

or

``easy_install pyramid_heroku``

-------------
Compatibility
-------------

pyramid_heroku runs with pyramid>=1.7 and python>=2.7 and python>=3.5.
Other versions might also work.

-------------
Documentation
-------------

Usage example for tweens::

    def main(global_config, **settings):$ cat .heroku/release.sh
        config = Configurator(settings=settings)
        config.include('pyramid_heroku.client_addr')
        config.include('pyramid_heroku.herokuapp_access')
        return config.make_wsgi_app()

The `pyramid_heroku.herokuapp_access` tween depends on
`pyramid_heroku.client_addr` tween and it requires you to list whitelisted IPs
in the `pyramid_heroku.herokuapp_whitelist` setting.

Usage example for automatic alembic migration script::

    $ cat .heroku/release.sh
    #!/usr/bin/env bash

    set -e

    echo "Running migrations"
    python -m pyramid_heroku.migrate my_app etc/production.ini app:main

    echo "DONE!"

For migration script to work, you need to set the ``MIGRATE_API_SECRET_HEROKU``
env var in Heroku. This allows the migration script to use the Heroku API.

See tests for more examples.

If you use structlog, add the following configuration setting to your INI file to enable structlog-like logging::

    pyramid_heroku.structlog = true


Releasing
---------

#. Update CHANGES.rst.
#. Update setup.py version.
#. Run ``bin/longtest``.
#. Run ``python setup.py sdist upload``.
