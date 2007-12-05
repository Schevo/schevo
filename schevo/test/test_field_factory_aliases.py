"""Field factory deprecated name tests.

For copyright, license, and warranty, see bottom of file.
"""

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

# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
