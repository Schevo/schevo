from schevo.schema import *
schevo.schema.prep(locals())

import random
import string


class Frob(E.Entity):
    """Some sort of something that has four holes."""

    name = f.string()

    _key(name)

    _sample_unittest = [
        ('Frob 1',),
        ('Frob 2',),
        ('Frob 3',),
        ('Frob 4',),
        ]

    _sample_unittest_priority = 1

    def q_hole_details(self):
        def fn():
            details = []
            for hole in self.m.holes():
                if hole.thread_count == 0:
                    details.append(hole.v.detail())
                else:
                    details.extend(
                        hole.v.detail(thread)
                        for thread
                        in hole.m.threads('hole_a') + hole.m.threads('hole_b')
                        )
            return details
        return Q.Simple(fn, 'Hole Details')

    class _Create(T.Create):

        def _after_execute(self, db, frob):
            # Create holes 1, 2, 3, and 4.
            for number in xrange(1, 5):
                db.execute(db.Hole.t.create(
                    frob=frob,
                    number=number,
                    ))


class Hole(E.Entity):
    """A hole on a frob."""

    frob = f.entity('Frob', on_delete=CASCADE)
    number = f.integer()
    @f.integer()
    def thread_count(self):
        return self.s.count('Thread')

    _key(frob, number)

    _hide('t_create', 't_delete')

    def v_detail(self, thread=None):
        return E.Hole._Detail(self, thread)

    class _Detail(V.View):

        @f.entity('Hole')
        def from_hole(self):
            return self.s.entity
        thread = f.entity('Thread')
        to_hole = f.entity('Hole')
        @f.float()
        def thickness(self):
            return getattr(self.thread, 'thickness', UNASSIGNED)

        @selectionmethod
        def t_delete_selected_threads(cls, selection):
            return cls._DeleteSelectedThreads(selection)

        def _setup(self, entity, thread=None):
            if thread is not None:
                self.thread = thread
                if thread.hole_a == self.s.entity:
                    self.to_hole = thread.hole_b
                else:
                    self.to_hole = thread.hole_a

        class _DeleteSelectedThreads(T.DeleteSelected):

            def _setup(self):
                self._selection = [
                    detail.thread for detail in self._selection
                    ]


class Pairing(E.Entity):
    """A pairing between two frobs."""

    frob = f.entity('Frob')
    mate = f.entity('Frob')

    _key(frob)

    _sample_unittest = [
        dict(frob=('Frob 1',),
             mate=('Frob 4',),
             ),
        dict(frob=('Frob 3',),
             mate=('Frob 2',),
             ),
        ]

    class _Create(T.Create):

        def _setup(self):
            self.x.need_reverse = True

        def _after_execute(self, db, pairing):
            # Create a reverse pairing.
            if self.x.need_reverse:
                tx = db.Pairing.t.create(
                    frob=pairing.mate,
                    mate=pairing.frob,
                    )
                tx.x.need_reverse = False
                db.execute(tx)


class Thread(E.Entity):
    """A piece of string between two holes."""

    hole_a = f.entity('Hole')
    hole_b = f.entity('Hole')
    thickness = f.float()

    _key(hole_a, hole_b)

    _sample_unittest = [
        dict(hole_a=dict(frob=('Frob 1',), number=1),
             hole_b=dict(frob=('Frob 2',), number=1),
             thickness=1.0,
             ),
        dict(hole_a=dict(frob=('Frob 1',), number=1),
             hole_b=dict(frob=('Frob 3',), number=2),
             thickness=1.1,
             ),
        dict(hole_a=dict(frob=('Frob 1',), number=1),
             hole_b=dict(frob=('Frob 4',), number=3),
             thickness=1.2,
             ),
        dict(hole_a=dict(frob=('Frob 2',), number=2),
             hole_b=dict(frob=('Frob 2',), number=3),
             thickness=1.3,
             ),
        dict(hole_a=dict(frob=('Frob 2',), number=3),
             hole_b=dict(frob=('Frob 3',), number=1),
             thickness=1.4,
             ),
        dict(hole_a=dict(frob=('Frob 3',), number=3),
             hole_b=dict(frob=('Frob 4',), number=4),
             thickness=1.5,
             ),
        ]


def t_create_random_frob(name_length=16):
    tx = db.Frob.t.create()
    tx.name = ''.join(
        random.choice(string.uppercase) for x in xrange(name_length))
    relabel(tx, 'Create Random Frob')
    return tx
