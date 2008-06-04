"""Create database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script.db_evolve import evolve_db
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db create [options] DBFILE

DBFILE: The database file to create.

At a minimum, either the --app or the --schema option must be specified.
"""


def _parser():
    p = opt.parser(usage)
    p.add_option('-a', '--app',
                 dest='app_path',
                 help='Use application in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-c', '--icons',
                 dest='icon_path',
                 help='Use icons from PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-e', '--evolve-from-version',
                 dest='evolve_from_version',
                 help='Begin database evolution at VERSION.',
                 metavar='VERSION',
                 default='latest',
                 )
    p.add_option('-p', '--sample',
                 dest='create_sample_data',
                 help='Create sample data.',
                 action='store_true',
                 default=False,
                 )
    p.add_option('-s', '--schema',
                 dest='schema_path',
                 help='Use schema in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-v', '--version',
                 dest='schema_version',
                 help='Evolve database to VERSION.',
                 metavar='VERSION',
                 default='latest',
                 )
    p.add_option('-x', '--delete',
                 dest='delete_existing_database',
                 help='Delete existing database file if one exists.',
                 action='store_true',
                 default=False,
                 )
    return p


class Create(Command):

    name = 'Create Database'
    description = 'Create a new database.'

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
        # Delete the database file if one exists.
        if options.delete_existing_database:
            if os.path.isfile(db_filename):
                print 'Deleting existing file:', db_filename
                os.remove(db_filename)
        # Use a default backend if one was not specified on the
        # command-line.
        if options.backend_name is None:
            options.backend_name = os.environ.get(
                'SCHEVO_DEFAULT_BACKEND', 'durus')
        # Create the database.
        if os.path.isfile(db_filename):
            parser.error(
                'Use "schevo db update" or "schevo db evolve" commands to '
                'update or evolve an existing database.')
        final_version = options.schema_version.lower()
        if final_version != 'latest':
            try:
                final_version = int(final_version)
            except ValueError:
                parser.error(
                    'Please specify a version number or "latest" '
                    'for the --version option.')
        else:
            final_version = schevo.schema.latest_version(schema_path)
        evolve_from_version = options.evolve_from_version.lower()
        if evolve_from_version != 'latest':
            try:
                evolve_from_version = int(evolve_from_version)
            except ValueError:
                parser.error(
                    'Please specify a version number or "latest" '
                    'for the --evolve-from-version option.')
        else:
            evolve_from_version = schevo.schema.latest_version(schema_path)
        if evolve_from_version > final_version:
            # Respect the version number given by --version over the
            # version number given by --evolve-from-version.
            evolve_from_version = final_version
        print 'Creating new database at version %r.' % evolve_from_version
        schema_source = schevo.schema.read(
            schema_path, version=evolve_from_version)
        db = schevo.database.create(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            schema_source=schema_source,
            schema_version=evolve_from_version,
            )
        # Evolve if necessary.
        if final_version > evolve_from_version:
            print 'Evolving database...'
            evolve_db(parser, schema_path, db, final_version)
        # Import icons.
        if icon_path and os.path.exists(icon_path):
            print 'Importing icons...'
            schevo.icon.install(db, icon_path)
        # Create sample data.
        if options.create_sample_data:
            print 'Populating with sample data...'
            db.populate()
        # Pack the database.
        print 'Packing the database...'
        db.pack()
        # Done.
        print 'Database version is now at %i.' % db.version
        db.close()
        print 'Database created.'


start = Create


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
