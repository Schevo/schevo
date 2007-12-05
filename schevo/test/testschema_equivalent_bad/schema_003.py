"""Evolution test schema, version 3."""

# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


class Foo(E.Entity):

    name = f.string()

    _key(name)

    _initial = [
        (u'two', ),
        (u'one', ),
        (u'four', ),
        (u'three', ),
        (u'five', ),
        ]


def after_evolve(db):
    db.execute(db.Foo.t.create(name='nine'))
