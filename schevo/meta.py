"""Metaclasses.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevo.fieldspec import field_spec_from_class
from schevo.label import label_from_name
import schevo.namespace


def schema_metaclass(namespace_name):
    """Return a metaclass that adds subclasses to a namespace of a
    SchemaDefinition."""
    class Meta(type):
        def __init__(cls, class_name, bases, class_dict):
            type.__init__(cls, class_name, bases, class_dict)
            # Assign a label for the class.
            if '_label' not in class_dict:
                cls._label = label_from_name(class_name)
            # Only if this global schema definition variable exists.
            if (schevo.namespace.SCHEMADEF is not None
                and hasattr(cls, '_field_spec')
                ):
                # Create an initial field spec odict, which will get
                # updated by the EntityMeta class.
                cls._field_spec = field_spec_from_class(cls, class_dict)
                # Add this class to the namespace.
                ns = getattr(
                    schevo.namespace.SCHEMADEF, namespace_name)
                try:
                    ns._set(class_name, cls)
                except KeyError:
                    # Skip private classes.
                    pass
    return Meta


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
