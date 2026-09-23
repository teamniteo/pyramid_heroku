pyramid_heroku
==============

Introduction
------------

pyramid_heroku is a collection of tweens and helpers to successfully run `Pyramid <http://www.trypyramid.com/>`_ on `Heroku <https://heroku.com/>`_

It provides the following:

* ``ClientAddr`` tween that sets real user's IP to ``request.client_addr``. Without this tween you cannot do IP-based geolocation, IP allowlisting, etc.
* ``Host`` tween that sets `request.host` to proxied `X-Forwarded-Host` header (note: potential security risk)
* ``HerokuappAccess`` tween that denies access to your app's ``<app>.herokuapp.com`` domain, or ``<app>.fly.dev`` on Fly.io, for any non-allowlisted IPs. This is helpful because you don't want anyone outside your team (i.e. usual visitors/users and search bots) to be able to visit the platform's own hostname besides the domain the app is deployed on. This is for security and SEO purposes.
* ``migrate.py`` script for automatically running alembic migrations on deploy.
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

The ``pyramid_heroku.herokuapp_access`` tween requires you to list allowlisted
IPs in the ``pyramid_heroku.herokuapp_allowlist`` setting. On Heroku it depends
on the ``pyramid_heroku.client_addr`` tween to know who the caller is. A bypass
is possible by setting the `HEROKUAPP_ACCESS_BYPASS` environment variable to a
secret value and then sending a request with the `User-Agent` header set to the
same secret value.

It gates ``herokuapp.com`` by default. To gate another platform's hostname, name
it; this replaces the default rather than adding to it, and matches whole domain
labels, so ``fly.dev`` matches ``foo.fly.dev`` but not ``fly.dev.attacker.example``::

    pyramid_heroku.herokuapp_hosts = fly.dev

On Fly.io the caller is not in ``X-Forwarded-For``, which Fly's proxy rewrites
to its own address, but in ``Fly-Client-IP``, which Fly overwrites on every
request. Tell the tween to read it from there, and skip the ``client_addr``
tween::

    pyramid_heroku.client_addr_header = Fly-Client-IP

Only set ``client_addr_header`` on a platform that guarantees the header, since
anywhere else the caller can send it themselves. An app running on both
platforms during a migration can name both hosts, whitespace separated, and set
the header setting from the environment so that it is only present on Fly.

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
