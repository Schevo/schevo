"""Update database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database
import schevo.error
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db update [options] DBFILE

DBFILE: The database file to update.

At a minimum, either the --app or the --schema option must be specified.
"""


def _parser():
    p = opt.parser(usage)
    p.add_option('-a', '--app', dest='app_path',
                 help='Use application in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-c', '--icons', dest='icon_path',
                 help='Use icons from PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-s', '--schema', dest='schema_path',
                 help='Use schema in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    return p


class Update(Command):

    name = 'Update Database'
    description = 'Update an existing database.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify DBFILE.')
        db_filename = args[0]
        # Process paths.  Start with app_path option and populate
        # schema_path and icon_path based on it if it is set, then use
        # icon_path and schema_path options to override.
        icon_path = None
        schema_path = None
        if options.app_path:
            app_path = package_path(options.app_path)
            icon_path = os.path.join(app_path, 'icons')
            schema_path = os.path.join(app_path, 'schema')
        if options.icon_path:
            icon_path = package_path(options.icon_path)
        if options.schema_path:
            schema_path = package_path(options.schema_path)
        if schema_path is None:
            parser.error('Please specify either the --app or --schema option.')
        # Open the database.
        if not os.path.isfile(db_filename):
            parser.error('DBFILE must be an existing database.')
        print 'Opening database...'
        db = schevo.database.open(db_filename)
        print 'Current database version is %i.' % db.version
        try:
            schema_source = schevo.schema.read(schema_path, version=db.version)
        except schevo.error.SchemaFileIOError:
            parser.error('Could not read schema source for version %i.'
                         % db.version)
        print 'Syncing database with new schema source...'
        db._sync(schema_source, initialize=False)
        # Import icons.
        if icon_path and os.path.exists(icon_path):
            print 'Importing icons...'
            schevo.icon.install(db, icon_path)
        # Pack the database.
        print 'Packing the database...'
        db.pack()
        # Done.
        db.close()
        print 'Database updated.'


start = Update


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
