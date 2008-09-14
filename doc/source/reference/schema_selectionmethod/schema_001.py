from schevo.schema import *
schevo.schema.prep(locals())


class Cog(E.Entity):

    name = f.string()


class Sprocket(E.Entity):

    cog = f.entity('Cog')
    sequence = f.integer()

    _hide('t_delete')
