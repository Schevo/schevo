"""Description of schema."""

# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


class Bar(E.Entity):

    name = f.string()
