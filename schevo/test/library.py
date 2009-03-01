"""Library of unit tests that use a storage backend.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.backend import backends
from schevo.test import CreatesDatabase, CreatesSchema, EvolvesSchemata


storage_test_classes = {
    # format: (module_name, class_name, class),
    }


def _add_modules(*modules):
    for module in modules:
        module_name = module.__name__
        for key, value in module.__dict__.iteritems():
            if (isinstance(value, type)
                and getattr(value, 'include', None) == True
                ):
                L = storage_test_classes.setdefault(value.format, [])
                L.append((module_name, key, value))


def storage_classes(class_label, backend_name, format, backend_args={}):
    BackendClass = backends[backend_name]
    new_classes = {}
    for module_name, class_name, base_class in storage_test_classes[format]:
        if issubclass(base_class, EvolvesSchemata):
            class TestClass(base_class):

                def _open(self, reopening=False, base_class=base_class):
                    db = base_class._open(self)
                    return self._assign_module_globals(db)

                def _assign_module_globals(self, db, base_class=base_class):
                    db_name = 'db'
                    ex_name = 'ex'
                    setattr(self, db_name, db)
                    modname = base_class.__module__
                    mod = sys.modules[modname]
                    setattr(mod, db_name, db)
                    setattr(mod, ex_name, db.execute)
                    return db

                def close(self, suffix='', base_class=base_class):
                    db_name = 'db'
                    base_class.close(self, suffix)
                    modname = base_class.__module__
                    mod = sys.modules[modname]
                    delattr(mod, db_name)

                def reopen(self, suffix='', format=None, base_class=base_class):
                    db = base_class.reopen(self, suffix, format)
                    return self._assign_module_globals(db, format)
            # We get a NameError if we assign these directly in the
            # definition of TestClass.
            TestClass.backend_name = backend_name
            TestClass.backend_args = backend_args
            TestClass.format = format
        elif issubclass(base_class, CreatesDatabase):
            class TestClass(base_class):

                def _open(self, suffix='', reopening=False,
                          base_class=base_class):
                    db = base_class._open(self, suffix)
                    return self._assign_module_globals(db, suffix)

                def _assign_module_globals(self, db, suffix,
                                           base_class=base_class):
                    db_name = 'db' + suffix
                    ex_name = 'ex' + suffix
                    setattr(self, db_name, db)
                    modname = base_class.__module__
                    mod = sys.modules[modname]
                    setattr(mod, db_name, db)
                    setattr(mod, ex_name, db.execute)
                    return db

                def close(self, suffix='', base_class=base_class):
                    db_name = 'db' + suffix
                    base_class.close(self, suffix)
                    modname = base_class.__module__
                    mod = sys.modules[modname]
                    delattr(mod, db_name)

                def reopen(self, suffix='', format=None, base_class=base_class):
                    print 'reopening'
                    db = base_class.reopen(self, suffix, format)
                    return self._assign_module_globals(db, suffix)
            # See above.
            TestClass.backend_name = backend_name
            TestClass.backend_args = backend_args
            TestClass.format = format
        TestClass.__name__ = '%s:%s:%s' % (
            class_label, module_name, class_name)
        TestClass.__test__ = True
        new_classes[TestClass.__name__] = TestClass
    return new_classes


from schevo.test import (
    test_bank,
    test_calculated_field_unicode,
    test_change,
    # test_convert_format,         <-- not format-specific
    test_database,
    test_database_namespace,
    test_default_values,
    test_entity_extent,
    test_entity_subclass,
    # test_equivalent,
    test_evolve,
    test_extent_name_override,
    test_extent_without_fields,
    test_extentmethod,
    test_field_entity,
    test_field_entitylist,
    test_field_entityset,
    test_field_entitysetset,
    test_field_maps,
    test_field_metadata_changed,
    test_find_algorithm,
    test_icon,
    test_label,
    test_links,
    test_on_delete,
    test_populate,
    test_prefix,
    test_query,
    test_relax_index,
    test_schema,
    test_transaction,
    test_transaction_before_after,
    test_transaction_cdu_subclass,
    test_transaction_field_reorder,
    test_transaction_requires_changes,
    test_valid_values_resolve,
    test_view,
    )


_add_modules(
    test_bank,
    test_calculated_field_unicode,
    test_change,
    # test_convert_format,         <-- not format-specific
    test_database,
    test_database_namespace,
    test_default_values,
    test_entity_extent,
    test_entity_subclass,
    # test_equivalent,
    test_evolve,
    test_extent_name_override,
    test_extent_without_fields,
    test_extentmethod,
    test_field_entity,
    test_field_entitylist,
    test_field_entityset,
    test_field_entitysetset,
    test_field_maps,
    test_icon,
    test_label,
    test_links,
    test_on_delete,
    test_populate,
    test_prefix,
    test_query,
    test_relax_index,
    test_schema,
    test_transaction,
    test_transaction_before_after,
    test_transaction_cdu_subclass,
    test_transaction_field_reorder,
    test_transaction_requires_changes,
    test_view,
    )


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2009 ElevenCraft Inc.
#
# Schevo
# http://schevo.org/
#
# ElevenCraft Inc.
# Bellingham, WA
# http://11craft.com/
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
