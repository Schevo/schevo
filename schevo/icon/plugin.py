"""Schevo icon loader for filesystems.

For copyright, license, and warranty, see bottom of file.
"""

import glob
import os

from schevo.icon import DEFAULT_PNG


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
        for filename in glob.glob(mask):
            # Strip extension.
            name, ext = os.path.splitext(os.path.basename(filename))
            # Read the file.
            f = file(filename, 'rb')
            png = f.read()
            f.close()
            # Store it in the SchevoIcon extent.
            if not db.SchevoIcon.find(name=name):
                tx = db.SchevoIcon.t.create_or_update()
                tx.name = name
                tx.data = png
                icon = db.execute(tx)

    def icon(self, name, use_default=True):
        icon = self.db.SchevoIcon.findone(name=name)
        if icon is None:
            if use_default:
                return DEFAULT_PNG
            else:
                return None
        else:
            return icon.data


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
