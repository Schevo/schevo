"""Schevo icon loader for filesystems."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import glob
import os

from schevo.icon import DEFAULT_PNG
from schevo.transaction import Combination


def install(db, icon_path=None):
    """Install an icon plugin in `db` if one does not yet exist."""
    # Install plugin.
    Plugin(db)
    # Sync if requested and plugin installed successfully.
    if icon_path and hasattr(db, '_icon'):
        db._sync_icons(icon_path)


class Plugin(object):

    def __init__(self, db):
        self.db = db
        # Don't install if db already has an icon plugin.
        if hasattr(db, '_icon'):
            return
        if 'SchevoIcon' in db.extent_names():
            db._plugins.append(self)
            db._icon = self.icon
            db._sync_icons = self.sync_icons

    def close(self):
        pass

    def sync_icons(self, icon_path):
        icon_path = str(icon_path)
        db = self.db
        mask = os.path.join(icon_path, '*.png')
        transactions = []
        for filename in glob.glob(mask):
            # Strip extension.
            name, ext = os.path.splitext(os.path.basename(filename))
            # Read the file.
            f = file(filename, 'rb')
            png = f.read()
            f.close()
            # Store it in the SchevoIcon extent.
            existing = db.SchevoIcon.findone(name=name)
            if existing is not None:
                if existing.data != png:
                    tx = existing.t.update(data=png)
                    transactions.append(tx)
            else:
                tx = db.SchevoIcon.t.create(name=name, data=png)
                transactions.append(tx)
        db.execute(Combination(transactions))

    def icon(self, name, use_default=True):
        icon = self.db.SchevoIcon.findone(name=name)
        if icon is None:
            if use_default:
                return DEFAULT_PNG
            else:
                return None
        else:
            return icon.data
