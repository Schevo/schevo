"""Schema definition unit tests."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

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
