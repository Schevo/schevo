"""Schevo base classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.


class Database(object):
    pass


class Entity(object):
    __slots__ = []


class Extent(object):
    pass


class Field(object):
    __slots__ = []


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
