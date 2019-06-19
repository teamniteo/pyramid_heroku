"""Tests for utils."""

import pytest


def test_safe_eval():
    """Test that dangerous values are safely eval-ed."""
    from pyramid_heroku import safe_eval

    assert safe_eval("False") is False
    assert safe_eval("True") is True
    assert safe_eval("false") is False
    assert safe_eval("true") is True
    assert safe_eval("1337") == 1337
    assert safe_eval("1337.1337") == 1337.1337
    assert safe_eval("asdfghjkl") == "asdfghjkl"
    assert safe_eval("asdfg hjkl") == "asdfg hjkl"
    assert safe_eval("'asdfg hjkl'") == "asdfg hjkl"
    assert safe_eval("u'true'") == "true"
    assert (
        safe_eval("raise Exception('Chrashed yet?')")
        == "raise Exception('Chrashed yet?')"
    )

    assert safe_eval("exit") == "exit"
    assert safe_eval("exit(12)") == "exit(12)"
    assert safe_eval("None") is None
    assert safe_eval("('test', 'tIsT')") == ("test", "tIsT")
    assert safe_eval("(('fOo', 'BaRrAr'), ('asd', 'AsD'))") == (
        ("fOo", "BaRrAr"),
        ("asd", "AsD"),
    )

    assert safe_eval("") == ""
    assert safe_eval("[]") == []
    with pytest.raises(ValueError):
        assert safe_eval(None) == []
    with pytest.raises(ValueError):
        assert safe_eval([1, 2, 3]) == []


def test_expandvars_dict():
    """Test that env vars are added to settings dict."""
    from pyramid_heroku import expandvars_dict
    import os

    os.environ["FOO"] = "foo"
    os.environ["BAR"] = "bar"
    os.environ["NESTED"] = "${FOO}bar"
    settings = {
        "test_boolean": "true",
        "test_integer": "1337",
        "test_string": "'asdfg hjkl'",
        "test_none": "None",
        "test_set": "('test', 'tIsT')",
        "test_multi_set": "(('fOo', 'BaRrAr'), ('asd', 'AsD'))",
        "test_empty": "",
        "test_env": "${FOO}",
        "test_env_nested": "${NESTED}",
        "test_dollar": "$",
        "test_endswith_dollar": "BAR$",
        "test_simple_variable": "$FOO",
        "test_multi_variables": "$FOO${BAR}",
        "test_default_set": "${FOO:-default}",
        "test_default_unset": "${BUZ:-default}",
        "test_substitute_set": "${FOO:+default}",
        "test_substitute_unset": "${BUZ:+default}",
        "test_offset": "${BAR:2}",
        "test_offset_length": "${BAR:1:3}",
    }

    expanded_settings = {
        "test_boolean": True,
        "test_integer": 1337,
        "test_string": "asdfg hjkl",
        "test_none": None,
        "test_set": ("test", "tIsT"),
        "test_multi_set": (("fOo", "BaRrAr"), ("asd", "AsD")),
        "test_empty": "",
        "test_env": "foo",
        "test_env_nested": "foobar",
        "test_dollar": "$",
        "test_endswith_dollar": "BAR$",
        "test_simple_variable": "foo",
        "test_multi_variables": "foobar",
        "test_default_set": "foo",
        "test_default_unset": "default",
        "test_substitute_set": "default",
        "test_substitute_unset": "",
        "test_offset": "r",
        "test_offset_length": "ar",
    }

    assert expanded_settings == expandvars_dict(settings)
