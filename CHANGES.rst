=======
Changes
=======

0.9.1
-----

 * Don't use Cloudflare IPs for client_addr. ClientAddr tween now sets a
   correct IP when using Cloudflare's reverse proxy. The tween fetches the list
   of Cloudflare's IPs on pyramid app start and ignores Cloudflare's IPs in
   `X-Forwarded-For` header.
   [am-on]

 * Bump year to 2022
   [am-on]

 * Rename niteoweb -> teamniteo
   [zupo]


0.8.0
-----

 * Do not touch Heroku maintenance mode during migration if it's already enabled.
   This helps when we want to enable/disable the maintenance mode manually or externally.
   [sayanarijit]

 * Add options to manually enable or disable Heroku maintenance mode.
   Use `pyramid_heroku.maintenance` script to manage the maintenance state.
   [sayanarijit]

 * Heroku API client related code has been moved from `pyramid_heroku.migrate` to
   `pyramid_heroku.heroku`, while the `shell` function is now in `pyramid_heroku`.
   [sayanarijit]


0.7.0
-----

 * Add `pyramid_heroku.Host` tween to support AutoIdle add-on. Refs:
   https://github.com/teamniteo/pyramid-realworld-example-app/issues/127
   [zupo]


0.6.0
-----

 * Update how alembic should be called in migrate.py. This is to reflect the
   latest changes to pyramid_deferred_sqla:
   https://github.com/teamniteo/pyramid_deferred_sqla/commit/b963702cab3934116fb00b6ef186959bc1627026
   [zupo]


0.5.0
-----

 * Prefer empty string than None. `{'VAL': '${VAR}'}` will expand into
   `{'VAL': ''}` instead of `{'VAL': None}` if the value of `VAR` is not exported or
   is an empty string.
   [sayanarijit]

 * To enforce that `$VAR` must be set, `${VAR:?custom error message}` syntax can be used.
   [sayanarijit]


0.4.0
-----

 * Supports bash style environment variable expansion.
   e.g. to declare default value, use `${DATABASE_URL:-sqlite:///database.db}`
   [sayanarijit]


0.3.2
-----

 * Shell now prints stderr/stdout even on non-zero exit code.
   [iElectric]


0.3.1
-----

 * Fix auth bug in migrate.py.
   [zupo]


0.3
---

 * Drop support for zc.buildout environments.
   [zupo]


0.2
---

* Expand all environment variables in the settings dictionary. This allows you
  to have, for example `${DATABASE_URL}` to get db connection string from
  environment into your `production.ini` file.
  [zupo]

* Use pipenv for setting up development.
  [zupo]

* Add basic type hinting.
  [zupo]

* Drop support for Python versions older than 3.7.
  [zupo]


0.1.5
-----

* Brown bag release.
  [karantan]


0.1.4
-----

* Fix return value in migrate.shell. `subprocess.check_output` changed in
  python 3.6 and is now returning byte and not str.
  [karantan]

0.1.3
-----

* Provided default values for migrate.py - https://github.com/teamniteo/pyramid_heroku/issues/2
  [enkidulan]

0.1.2
-----

* The request.client_addr cannot be set directly, so we need to go around.
  [zupo]


0.1.1
-----

* Fix tween paths.
  [zupo]



0.1
---

* Initial release.
  [dz0ny, zupo]

