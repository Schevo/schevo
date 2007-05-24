"""Schevo schema support.  Allows a declarative syntax and other
helpful shortcuts not directly supported by Python.  Use it by putting
the following lines at the top of your application schema modules.


# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


For copyright, license, and warranty, see bottom of file.
"""

__all__ = [
    '_hide',
    '_key',
    '_index',
    'ANY',
    'CASCADE',
    'DEFAULT',
    'REMOVE',
    'RESTRICT',
    'UNASSIGN',
    'UNASSIGNED',
    'extentmethod',
    'schevo',  # And, indirectly, 'schevo.error'.
    'with_label',
    ]

from glob import glob
import os
import sys

import schevo
from schevo.constant import (
    ANY,
    CASCADE,
    DEFAULT,
    REMOVE,
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

from schevo.entity import extentmethod
from schevo.lib import optimize

import inspect
import threading
from types import FunctionType, TypeType


# _hide provides support for hiding actions from user interfaces.
def _hide(*args):
    """Append names to list of hidden names."""
    clsLocals = inspect.currentframe(1).f_locals
    # XXX: see schevo.entity.Entity._hidden_*
    hidden_actions = clsLocals.setdefault(
        '_hidden_actions', set(['create_if_necessary', 'generic_update']))
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


# 'import_lock' is a lock that is acquired during a schema import,
# then released when the import is finished.  It is used to prevent
# the schevo.schema.* namespace from being clobbered if multiple
# threads are importing schemata simultaneously.
import_lock = threading.Lock()

def start(db=None, evolving=False):
    """Lock schema importing."""
    import_lock.acquire()
    schevo.namespace.SCHEMADB = db
    schevo.namespace.EVOLVING = evolving
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
    schevo.namespace.EVOLVING = False
    # Remove this class now that the schema has been processed.
    del schema_def.E.Entity
    # Force all Entity field classes to readonly.
    for entity_name in schema_def.E:
        EntityClass = schema_def.E[entity_name]
        for FieldClass in EntityClass._field_spec.itervalues():
            FieldClass.readonly = True
    # Add relationship metadata to each Entity class.
    for parent, spec in schema_def.relationships.iteritems():
        E = schema_def.E
        # Catch non-existence errors.
        parentClass = getattr(E, parent, None)
        if parentClass is None:
            raise schevo.error.ExtentDoesNotExist(parent)
        # Make sure spec is sorted in field definition order.
        other_map = {}
        for other_extent_name, other_field_name in spec:
            other_extent_field_set = other_map.setdefault(
                other_extent_name, set())
            other_extent_field_set.add(other_field_name)
        spec = []
        for other_extent_name, other_extent_field_set in other_map.items():
            other_class = getattr(E, other_extent_name)
            spec.extend(
                (other_extent_name, other_field_name)
                for other_field_name
                in other_class._field_spec
                if other_field_name in other_extent_field_set
                )
        # Record final spec.
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


# ----------------------------------------------------------------------------
# Functions useful for dealing with schema files:

def latest_version(location):
    """Return the latest version number available at the given location,
    or None if no schemata could be found."""
    version = 0
    while os.path.exists(schema_filepath(location, version+1)):
        version += 1
    if version == 0:
        return None
    return version

def name(version, prefix='schema'):
    """Return canonical name for schema version."""
    return '%s_%03i' % (prefix, version)

def path(location):
    """If location is a module or package, return its path; otherwise,
    return location."""
    from_list = location.split('.')[:1]
    try:
        pkg = __import__(location, {}, {}, from_list)
    except ImportError:
        return location
    return os.path.dirname(pkg.__file__)

def read(location, version):
    """Return text contents of the schema file version at location."""
    filepath = schema_filepath(location, version)
    try:
        schema_file = file(filepath, 'rU')
        schema_source = schema_file.read()
    except IOError:
        raise schevo.error.SchemaFileIOError(
            'Could not open schema file %r' % filepath)
    schema_file.close()
    return schema_source

def schema_filepath(location, version, prefix=None):
    """Return the path of a specific schema version contained within
    the given location."""
    if prefix is None:
        prefix = schema_filename_prefix(location)
    return os.path.join(path(location), name(version, prefix) + '.py')


def schema_filename_prefix(location):
    """Return the schema filename prefix used at `location`.

    Raises `SchemaFileIOError` if duplicates are found.
    """
    # Find the prefix of the first version of the schema.
    suffix = '_001.py'
    suffixlen = len(suffix)
    globspec = os.path.join(path(location), '*' + suffix)
    matches = glob(globspec)
    if len(matches) == 0:
        raise schevo.error.SchemaFileIOError(
            'Could not find a version 1 schema at %r.'
            % location)
    elif len(matches) > 1:
        raise schevo.error.SchemaFileIOError(
            'Found more than one version 1 schemata at %r.'
            % location)
    prefix = os.path.basename(matches[0])[:-suffixlen]
    # Make sure same prefix is used for rest of schemata.
    version = 2
    while True:
        # Look for files matching this suffix.
        suffix = '_%03i.py' % version
        globspec = os.path.join(path(location), '*' + suffix)
        matches = glob(globspec)
        if len(matches) == 0:
            break
        if len(matches) > 1:
            raise schevo.error.SchemaFileIOError(
                'Found more than one version %i schemata at %r.'
                % (version, location))
        prefix2 = os.path.basename(matches[0])[:-suffixlen]
        if prefix2 != prefix:
            raise schevo.error.SchemaFileIOError(
                'Filename at version %i does not match version 1 prefix %r '
                'at %r.'
                % (version, prefix, location))
        version += 1
    # Everything checks out.
    return prefix


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
