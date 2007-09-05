"""Description of module.

For copyright, license, and warranty, see bottom of file.
"""

from schevo.script.command import CommandSet
from schevo.script import (
    db_compare,
    db_convert,
    db_copy,
    db_create,
    db_inject,
    db_evolve,
    db_update,
    )


class Database(CommandSet):

    name = 'Database Activities'
    description = 'Perform actions on Schevo databases.'

    def __init__(self):
        self.commands = {
            'compare': db_compare.start,
            'convert': db_convert.start,
            'copy': db_copy.start,
            'create': db_create.start,
            'inject': db_inject.start,
            'evolve': db_evolve.start,
            'update': db_update.start,
            }


start = Database


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
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
