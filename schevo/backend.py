"""Backend management and selection."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

backends = {}

try:
    import pkg_resources
except IOError, e:
    # If a custom distutils is included in a py2exe-generated library,
    # an IOError will occur when we try to find backends.  Silently
    # pass on this IOError.  py2exe main scripts should manually import
    # the plugin class and register it, like so::
    #
    #     from schevodurus.backend import DurusBackend
    #     from schevo.backend import backends
    #     backends['durus'] = DurusBackend
    pass
else:
    backends = dict(
        # backend-name=backend-class,
        (p.name, p.load())
        for p in pkg_resources.iter_entry_points('schevo.backend')
        )


def test_backends_dict():
    """Built-in backend is always present after Schevo is installed."""
    assert 'schevo.store' in backends


optimize.bind_all(sys.modules[__name__])  # Last line of module.
