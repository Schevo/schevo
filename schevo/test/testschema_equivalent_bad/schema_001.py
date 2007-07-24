"""Evolution test schema, version 1."""

# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


class Foo(E.Entity):

    name = f.unicode()

    _key(name)

    _initial = [
        (u'one', ),
        (u'two', ),
        (u'three', ),
        ]
