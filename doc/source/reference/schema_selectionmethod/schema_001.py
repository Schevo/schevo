from schevo.schema import *
schevo.schema.prep(locals())


class Cog(E.Entity):

    name = f.string()

    @selectionmethod
    def t_placeholder_a(self, selection):
        pass

    def v_backwards_name(self):
        return E.Cog._BackwardsName(self)

    class _BackwardsName(V.View):

        name = f.string()

        def _setup(self, entity):
            self.name = ''.join(reversed(entity.name))

        @selectionmethod
        def t_placeholder_b(self, selection):
            pass


class Sprocket(E.Entity):

    cog = f.entity('Cog')
    sequence = f.integer()

    _hide('t_delete')
