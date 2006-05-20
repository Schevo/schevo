"""Schevo base classes.

For copyright, license, and warranty, see bottom of file.
"""


class Database(object):
    pass


class Entity(object):
    __slots__ = []


class Extent(object):
    pass


class Field(object):
    pass


class Query(object):
    pass


class Results(object):
    pass


class Transaction(object):
    pass


class View(object):
    pass


# Useful for isinstance(obj, schevo.base.classes).
classes = (
    Database,
    Entity,
    Extent,
    Field,
    Query,
    Results,
    Transaction,
    View,
    )

classes_using_fields = (
    Entity,
    Transaction,
    View,
    # schevo.query.Param is dynamically added upon importing the
    # schevo.query module.
    )

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
