"""Schevo schema support.  Allows a declarative syntax and other
helpful shortcuts not directly supported by Python.  Use it by putting
the following lines at the top of your application schema modules.


# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


For copyright, license, and warranty, see bottom of file.
"""

__all__ = [
    '_export_all',
    '_import',
    '_hide',
    '_key',
    '_index',
    'ANY',
    'CASCADE',
    'DEFAULT',
    'RESTRICT',
    'UNASSIGN',
    'UNASSIGNED',
    'extentmethod',
    'prep',
    'schevo',  # And, indirectly, 'schevo.error'.
    'with_label',
    ]

import os
import pkg_resources
import sys

import schevo
from schevo.constant import (
    ANY,
    CASCADE,
    DEFAULT,
    RESTRICT,
    UNASSIGN,
    UNASSIGNED,
    )
from schevo.label import with_label

import schevo.base
import schevo.entity
import schevo.error
import schevo.field
import schevo.label
import schevo.namespace
import schevo.query
import schevo.transaction
import schevo.view

from schevo.lib import optimize

import inspect
import threading
from types import FunctionType, TypeType


# extentmethod provides support for decorating methods of entity
# classes as belonging to the extent, not the entity.
def extentmethod(fn):
    def outer_fn(cls, *args, **kw):
        return fn(cls._extent, *args, **kw)
    if hasattr(fn, '_label'):
        _plural = getattr(fn, '_plural', None)
        decorator = schevo.label.with_label(fn._label, _plural)
        outer_fn = decorator(outer_fn)
    outer_fn = classmethod(outer_fn)
    return outer_fn


# _hide provides support for hiding actions from user interfaces.
def _hide(*args):
    """Append names to list of hidden names."""
    clsLocals = inspect.currentframe(1).f_locals
    # XXX: see schevo.entity.Entity._hidden_*
    hidden_actions = clsLocals.setdefault(
        '_hidden_actions', set(['create_if_necessary', 'create_or_update']))
    hidden_queries = clsLocals.setdefault('_hidden_queries', set([]))
    hidden_views = clsLocals.setdefault('_hidden_views', set())
    for name in args:
        if name.startswith('q_'):
            hidden_queries.add(name[2:])
        elif name.startswith('t_'):
            hidden_actions.add(name[2:])
        elif name.startswith('v_'):
            hidden_views.add(name[2:])


# _key provides support for Entity key specification.
def _key(*args):
    """Append a key spec to the Entity subclass currently being
    defined."""
    clsLocals = inspect.currentframe(1).f_locals
    spec = clsLocals.setdefault('_key_spec_additions', [])
    spec.append(args)


# _index provides support for Entity index specification.
def _index(*args):
    """Append an index spec to the Entity subclass currently being
    defined."""
    clsLocals = inspect.currentframe(1).f_locals
    spec = clsLocals.setdefault('_index_spec_additions', [])
    spec.append(args)


def _import(requirement, name, version, *args, **kw):
    """Import an external schema in the schema currently being loaded.

    1. Makes sure the package ``requirement`` is satisfied.

    2. Loads the schema called ``name`` whose version is ``version``.
       This is dereferenced to a specific schema module using entry
       points defined by the requirement.

    3. Calls the ``_export`` function defined in that schema, passing
       it the global namespace of the schema that called _import,
       plus ``*args`` and ``**kw``.

    Implementation note: If the ``_globals`` keyword argument is
    defined, it will be used instead of the calling frame's globals.
    This is for use in backwards-compatibility functions such as
    `schevo.icon.schema.use`.
    """
    # Get the distribution that has the schema.
    dist = pkg_resources.require(requirement)[0]
    # Find the module name of the schema.
    entry_map = dist.get_entry_map('schevo.schema_export')
    entry_point = entry_map[name]
    pkgname = entry_point.module_name
    # Append the schema version to it.
    modname = '%s.schema_%03i' % (pkgname, version)
    # Get the module from _imported_schemata, since it's already been
    # imported by the database before _import is actually called.
    mod = schevo.namespace.SCHEMADB._imported_schemata[
        (requirement, name, version)]
    # Call upon the module to export.
    globals = kw.get('_globals', None)
    if not globals:
        globals = inspect.currentframe(1).f_globals
    mod._export(globals, *args, **kw)


def _export_all(namespace_to, namespace_from, **kw):
    """Exports all entity classes defined in ``namespace_from`` to
    ``namespace_to`` by creating subclasses.

    Various keyword arguments are supported:

    - ``hidden``: If set to True, then all subclasses created are set
      as hidden.
    """
    hidden = kw.get('hidden', False)
    for name, obj in namespace_from.iteritems():
        if (isinstance(obj, type)
            and issubclass(obj, schevo.entity.Entity)
            and not name.startswith('_')
            ):
            class Subclass(obj):
                _actual_name = name
                if hidden:
                    _hidden = True
            namespace_to[name] = Subclass


# 'import_lock' is a lock that is acquired during a schema import,
# then released when the import is finished.  It is used to prevent
# the schevo.schema.* namespace from being clobbered if multiple
# threads are importing schemata simultaneously.
import_lock = threading.Lock()

def start(db=None):
    """Lock schema importing."""
    import_lock.acquire()
    schevo.namespace.SCHEMADB = db
    if db:
        db._imported_schemata = {}

def prep(schema_namespace):
    """Add syntax support magic to the schema namespace."""
    # Set the global SCHEMADEF.
    schevo.namespace.SCHEMADEF = schevo.namespace.SchemaDefinition()
    schema_def = schevo.namespace.SCHEMADEF
    # Add this initial value that can't be added by the metaclass.
    schema_def.E.Entity = schevo.entity.Entity
    # Expose all builtin query classes.
    for k, v in schevo.query.__dict__.items():
        if (inspect.isclass(v)
            and issubclass(v, schevo.query.Query)
            ):
            schema_def.Q._set(k, v)
    # Expose all builtin transaction classes.
    for k, v in schevo.transaction.__dict__.items():
        if (inspect.isclass(v)
            and issubclass(v, schevo.transaction.Transaction)
            ):
            schema_def.T._set(k, v)
    # Expose all builtin view classes.
    for k, v in schevo.view.__dict__.items():
        if (inspect.isclass(v)
            and issubclass(v, schevo.view.View)
            ):
            schema_def.V._set(k, v)
    # Process the builtin fields now that we have a global SCHEMADEF.
    _field_info_extract(schevo.field)
    # Decorate the schema namespace.
    schema_namespace['d'] = schema_def
    schema_namespace['E'] = schema_def.E
    schema_namespace['F'] = schema_def.F
    schema_namespace['f'] = schema_def.f
    schema_namespace['Q'] = schema_def.Q
    schema_namespace['T'] = schema_def.T
    schema_namespace['V'] = schema_def.V
    # Expose the null database so that importing a Schevo schema
    # directly in Python, without a Schevo database, still succeeds.
    schema_namespace['db'] = _null_db

def finish(db, schema_module=None):
    """Unlock the schema import mutex and return the schema definition."""
    if schema_module is None:
        import_lock.release()
        return
    schema_def = schevo.namespace.SCHEMADEF
    # Reset the global namespace SCHEMADEF.
    schevo.namespace.SCHEMADEF = None
    schevo.namespace.SCHEMADB = None
    # Remove this class now that the schema has been processed.
    del schema_def.E.Entity
    # Add relationship metadata to each Entity class.
    for parent, spec in schema_def.relationships.iteritems():
        parentClass = getattr(schema_def.E, parent, None)
        if parentClass is None:
            raise schevo.error.ExtentDoesNotExist(parent)
        parentClass._relationships = spec
    del schema_def.relationships
    # Create database-level query function namespace.
    q = schema_def.q
    for name, func in schema_module.__dict__.iteritems():
        if isinstance(func, FunctionType) and name.startswith('q_'):
            # Strip q_ prefix.
            name = name[2:]
            # Give it a label if necessary.
            if getattr(func, '_label', None) is None:
                func._label = schevo.label.label_from_name(name)
            q._set(name, func)
    # Create database-level transaction function namespace.
    t = schema_def.t
    for name, func in schema_module.__dict__.iteritems():
        if isinstance(func, FunctionType) and name.startswith('t_'):
            # Strip t_ prefix.
            name = name[2:]
            # Give it a label if necessary.
            if getattr(func, '_label', None) is None:
                func._label = schevo.label.label_from_name(name)
            t._set(name, func)
    # Get rid of the temporary null database.
    del schema_module.db
    # Optimize the module.
    optimize.bind_all(schema_module)
    # Install the actual database.
    schema_module.db = db
    # Release import lock.
    import_lock.release()
    return schema_def


def _field_info_extract(module):
    """Extract field stuff to add to the schema definition namespace."""
    F_set = schevo.namespace.SCHEMADEF.F._set
    f_set = schevo.namespace.SCHEMADEF.f._set
    for FieldClass in module.__dict__.values():
        if (isinstance(FieldClass, TypeType)
            and issubclass(FieldClass, schevo.field.Field)
            ):
            # Add this class to the field classes namespace.
            F_set(FieldClass.__name__, FieldClass)
            # Add a field constructor to the field constructors namespace.
            f_set(FieldClass._def_name, FieldClass._def_class)


class _NullDatabase(object):
    """A dummy object to serve as the global 'db' var during schema
    loading."""

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kw):
        return self

_null_db = _NullDatabase()


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
