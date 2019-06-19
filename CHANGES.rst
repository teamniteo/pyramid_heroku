=======
Changes
=======

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

* Provided default values for migrate.py - https://github.com/niteoweb/pyramid_heroku/issues/2
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

