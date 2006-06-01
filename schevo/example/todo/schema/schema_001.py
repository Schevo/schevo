# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


class SchevoIcon(E.Entity):

    _hidden = True

    name = f.unicode()
    data = f.image()

    _key(name)


class Gender(E.Entity):
    """Gender of a person."""

    code = f.unicode()
    name = f.unicode()

    @f.integer(label=u'Person Count')
    def count(self):
        return self.sys.count('Person', 'gender')

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
    name = f.unicode()
    topic = f.entity('Topic', required=False)
    priority = f.entity('Priority')
    person = f.entity('Person', required=False)
    notes = f.memo(required=False)


class Person(E.Entity):
    """Individual human being."""

    _plural = u'People'

    name = f.unicode()
    gender = f.entity('Gender')

    _key(name)


class Priority(E.Entity):
    """Time-criticalness of a todo item."""

    _plural = u'Priorities'

    code = f.integer()
    name = f.unicode()

    @f.integer(label=u'# Open Items')
    def open(self):
        return len([item for item in self.sys.links('Item', 'priority')
                    if not item.data.done])

    @f.integer(label=u'# Done Items')
    def done(self):
        return len([item for item in self.sys.links('Item', 'priority')
                    if item.data.done])
    
    _key(code)
    _key(name)

    def __str__(self):
        return '%s %s' % (self.code, self.name)

    
class Topic(E.Entity):
    """Subject area for todo items."""

    name = f.unicode()


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
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
