"""Various utilities."""

from ast import literal_eval
from expandvars import expandvars

import sys
import typing as t


def safe_eval(text: str) -> t.Optional[str]:
    """Safely evaluate `text` argument.

    `text` can be evaluated to string, number,
    tuple, list, dict, boolean, and None.
    Code `text[0].upper + text[1:]` is for lower case
    'false' or 'true' strings, it should not break anything.
    """
    if not isinstance(text, str):
        raise ValueError(f"Expected a string, got {type(text)} instead.")

    if len(text) == 0:
        return None

    try:
        return literal_eval(text[0].upper() + text[1:])
    except (ValueError, SyntaxError):
        return text


def expandvars_dict(settings: t.Dict[str, str]) -> t.Dict[str, t.Any]:
    """Expand strings or variables from the environment into equivalent python literals or strings.

    >>> from pyramid_heroku import expandvars_dict
    >>> from pprint import pprint
    >>> from unittest import mock
    >>> import os
    >>> with mock.patch.dict(os.environ,{'STRING':'text', 'BOOL': 'true', 'INT':'1', 'NESTED':'nested_${STRING}'}):
    ...    pprint(expandvars_dict({
    ...        "string": "foo",
    ...        "bool": "true",
    ...        "int": "1",
    ...        "default_string": "${FOO:-bar}",
    ...        "default_int": "${FOO:-2}",
    ...        "default_bool": "${FOO:-false}",
    ...        "env_string": "${STRING:-foo}",
    ...        "env_int": "${INT:-foo}",
    ...        "env_bool": "${BOOL:-foo}",
    ...        "nested": "${NESTED:-foo}",
    ...    }))
    {'bool': True,
     'default_bool': False,
     'default_int': 2,
     'default_string': 'bar',
     'env_bool': True,
     'env_int': 1,
     'env_string': 'text',
     'int': 1,
     'nested': 'nested_text',
     'string': 'foo'}
    """
    return {k: safe_eval(expandvars(expandvars(v))) for k, v in settings.items()}
