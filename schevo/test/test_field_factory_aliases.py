"""Field factory deprecated name tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.test import BaseTest


class TestFieldFactoryDeprecatedNames(BaseTest):
    """
    Change `showwarning` to record deprecation warnings somewhere
    other than stderr, so we can test the deprecation warning below::

        >>> import warnings
        >>> old_showwarning = warnings.showwarning
        >>> def showwarning(message, category, filename, lineno, file=None):
        ...     warnings.last_lineno = lineno
        ...     warnings.last_message = message
        >>> warnings.showwarning = showwarning

    Create a schema that has a custom field class, and uses it with both
    styles of field factory names::

        >>> body = '''
        ...     class SomeStringThing(F.String):
        ...         pass
        ...
        ...     class Foo(E.Entity):
        ...
        ...         name = f.some_string_thing()       # Preferred.
        ...         code = f.someStringThing()         # Deprecated.
        ...     '''

    When using the schema, a deprecation warning is given for the
    field definition that used the camelCase version of the name,
    which is now deprecated. The line number that the warning is on
    appears to be line eight above, but since a two-line header is
    prepended to the body during unit testing, it's actually line 10
    that the warning occurs at::

        >>> from schevo.test import DocTest
        >>> t = DocTest(body)
        >>> print warnings.last_message  #doctest: +ELLIPSIS
        'someStringThing' is a deprecated field definition name. ...
        >>> warnings.last_lineno
        10

    Place the old `showwarning` function back into the `warnings` module::

        >>> warnings.showwarning = old_showwarning
    """
