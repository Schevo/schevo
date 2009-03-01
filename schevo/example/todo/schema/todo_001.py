# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


class SchevoIcon(E.Entity):

    _hidden = True

    name = f.string()
    data = f.image()

    _key(name)


class Gender(E.Entity):
    """Gender of a person."""

    code = f.string()
    name = f.string()

    @f.integer(label=u'Person Count')
    def count(self):
        return self.s.count('Person', 'gender')

    _key(code)
    _key(name)

    _initial = [
        (u'F', u'Female'),
        (u'M', u'Male'),
        (u'U', u'Unknown'),
        ]


class Item(E.Entity):
    """Something that must be done."""

    done = f.boolean(default=False)
    name = f.string()
    topic = f.entity('Topic', required=False)
    priority = f.entity('Priority')
    person = f.entity('Person', required=False)
    notes = f.string(multiline=True, required=False)


class Person(E.Entity):
    """Individual human being."""

    _plural = u'People'

    name = f.string()
    gender = f.entity('Gender')

    _key(name)

    _sample = [
        ('Jane Doe', ('F',)),
        ('John Doe', ('M',)),
        ]


class Priority(E.Entity):
    """Time-criticalness of a todo item."""

    _plural = u'Priorities'

    code = f.integer()
    name = f.string()

    @f.integer(label=u'# Open Items')
    def open(self):
        return len([item for item in self.m.items() if not item.done])

    @f.integer(label=u'# Done Items')
    def done(self):
        return len([item for item in self.m.items() if item.done])

    _key(code)
    _key(name)

    _sample = [
        (1, 'Top'),
        (2, 'Mid'),
        (3, 'Low'),
        ]

    def __str__(self):
        return '%s %s' % (self.code, self.name)


class Topic(E.Entity):
    """Subject area for todo items."""

    name = f.string()

    _sample = [
        ('Home', ),
        ('Work', ),
        ]
