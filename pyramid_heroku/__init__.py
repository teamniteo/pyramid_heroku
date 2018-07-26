"""Various utilities."""

from ast import literal_eval

import os
import sys
import typing as t


def safe_eval(text: str) -> str:
    """Safely evaluate `text` argument.

    `text` can be evaluated to string, number,
    tuple, list, dict, boolean, and None.
    Code `text[0].upper + text[1:]` is for lower case
    'false' or 'true' strings, it should not break anything.
    """
    if not isinstance(text, str):
        raise ValueError(f"Expected a string, got {type(text)} instead.")

    try:
        if len(text) == 0:
            return None
        else:
            return literal_eval(text[0].upper() + text[1:])
    except (ValueError, SyntaxError):
        return text


def expandvars_dict(settings: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """Expand all environment variables in a settings dictionary.

    Env vars are expanded twice, so you can have (1-level) nesting. Example:

    $ export FOO='foo'
    $ export BAR='${FOO}bar'
    $ python
    >>> from pyramid_heroku import expandvars_dict
    >>> expandvars_dict({'my_var': '${BAR}'})
    {'my_var': 'foobar'}
    """
    return {
        key: safe_eval(os.path.expandvars(os.path.expandvars(value)))
        for (key, value) in settings.items()
    }
