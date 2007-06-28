"""Schema definition unit tests.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.lib import module
import schevo.schema


SCHEMA = """
from schevo.schema import *
schevo.schema.prep(locals())

# Verify that the name 'db' is accessible.
repr(db)
"""


def test_schema_db_reference():
    # Forget existing modules.
    for m in module.MODULES:
        module.forget(m)
    # Import schema.
    schema_module = None
    schevo.schema.start()
    try:
        schema_module = module.from_string(
            SCHEMA, 'test_schema_db_reference-schema')
        module.remember(schema_module)
    finally:
        schevo.schema.finish(schema_module)


# Copyright (C) 2001-2006 Orbtech, L.L.C.
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
