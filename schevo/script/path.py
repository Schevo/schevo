"""Path-handling functions for Schevo script commands."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import os


def package_path(pkg_or_path):
    """If pkg_or_path is a module, return its path; otherwise,
    return pkg_or_path."""
    from_list = pkg_or_path.split('.')[:1]
    try:
        pkg = __import__(pkg_or_path, {}, {}, from_list)
    except ImportError:
        return os.path.abspath(pkg_or_path)
    if '__init__.py' in pkg.__file__:
        # Package was specified; return the dir it's in.
        return os.path.abspath(os.path.dirname(pkg.__file__))
    else:
        # Module was specified; return its filename.
        return os.path.abspath(pkg.__file__)


optimize.bind_all(sys.modules[__name__])  # Last line of module.
