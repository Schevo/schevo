"""Schevo object decoration."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import re
import sys

from schevo.lib import optimize

from schevo.base import Field


# Modify this dictionary to map default labels to preferred labels.
PREFERRED_LABELS = {
    u'Create': u'New',
    u'Update': u'Edit',
    }


class LabelMixin(object):
    """Mix this in with classes that have labels themselves via a
    `_label` attribute, and whose instances have labels via a
    `__str__` method.

    Example: Entity.
    """
    __slots__ = []


def _preferred_label(obj):
    label = unicode(obj)
    if label in PREFERRED_LABELS:
        return PREFERRED_LABELS[label]
    else:
        return label


def label(obj):
    """Return the unicode label for `obj`.

    In the case of nouns, return the singular label.

    In the case of verbs, return the present tense form.
    """
    if isinstance(obj, LabelMixin):
        return _preferred_label(obj)
    elif hasattr(obj, '_label'):
        return _preferred_label(obj._label)
    elif hasattr(obj, 'label'):
        return _preferred_label(obj.label)
    else:
        return _preferred_label(obj)


def plural(obj):
    """Return the plural noun label for `obj`."""
    if hasattr(obj, '_plural'):
        return _preferred_label(obj._plural)


def label_from_name(name):
    """Return a label based on the given object name."""
    # Split on underscores, ignoring duplicate and leading
    # underscores.
    parts = [part for part in name.split('_') if part]
    if len(parts) > 1:
        # Capitalize each word.
        parts = (part[0].upper() + part[1:] for part in parts if part)
        # Treat _ as explicit space.
        name = ' '.join(parts)
    else:
        # Capitalize first letter.
        name = parts[0]
        name = name[0].upper() + name[1:]
        # Treat each capital letter as having an implicit space prefix.
        rawstr = '([A-Z][a-z]*)'
        compile_obj = re.compile(rawstr)
        parts = compile_obj.split(name)
        # Remove extraneous spaces.
        name = ' '.join(part for part in parts if part)
    return unicode(name)


def plural_from_name(name):
    """Return a plural label based on the given object name."""
    return label_from_name(name) + u's'


def relabel(obj, new_label):
    """Relabel an object with a new label."""
    if isinstance(obj, Field):
        obj.label = new_label
    elif isinstance(obj, type) and issubclass(obj, Field):
        obj.label = new_label
    else:
        obj._label = new_label


optimize.bind_all(sys.modules[__name__])  # Last line of module.
