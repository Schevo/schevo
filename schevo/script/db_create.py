"""Create database command.

For copyright, license, and warranty, see bottom of file.
"""

import os

import schevo.database
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo db create [options] DBFILE

DBFILE: The database file to create.

Either --app or --schema must be given at a minimum.

Note: Currently, only the schema_001.py file will be loaded from the
schema package."""


def _parser():
    p = opt.parser(usage)
    p.add_option('-a', '--app', dest='app_path',
                 help='Use application in PATH.',
                 metavar='PATH',
                 default=None
                 )
    p.add_option('-c', '--icons', dest='icon_path',
                 help='Use icons from PATH.',
                 metavar='PATH',
                 default=None
                 )
    p.add_option('-i', '--import', dest='import_from',
                 help='Import XML data previously exported to FILE.',
                 metavar='FILE',
                 default=None,
                 )
    p.add_option('-p', '--sample', dest='create_sample_data',
                 help='Create sample data.',
                 action='store_true',
                 default=False,
                 )
    p.add_option('-s', '--schema', dest='schema_path',
                 help='Use schema in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    p.add_option('-x', '--delete', dest='delete_existing_database',
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
        def path(pkg_or_path):
            """If pkg_or_path is a module, return its path; otherwise,
            return pkg_or_path."""
            from_list = pkg_or_path.split('.')[:1]
            try:
                pkg = __import__(pkg_or_path, {}, {}, from_list)
            except ImportError:
                return pkg_or_path
            if '__init__.py' in pkg.__file__:
                # Package was specified; return the dir it's in.
                return os.path.dirname(pkg.__file__)
            else:
                # Module was specified; return its filename.
                return pkg.__file__
        icon_path = None
        schema_path = None
        if options.app_path:
            app_path = path(options.app_path)
            icon_path = os.path.join(app_path, 'icons')
            schema_path = os.path.join(app_path, 'schema')
        if options.icon_path:
            icon_path = path(options.icon_path)
        if options.schema_path:
            schema_path = path(options.schema_path)
        schema_source = schevo.schema.read(schema_path, version=1)
        # Delete the database file if one exists.
        if options.delete_existing_database:
            if os.path.isfile(db_filename):
                print 'Deleting existing file:', db_filename
                os.remove(db_filename)
        # Create the database.
        if os.path.isfile(db_filename):
            print 'Opening the existing database...'
        else:
            print 'Creating a new database...'
        if options.import_from is not None:
            print 'Importing data from %r...' % options.import_from
            # Open the XML import file.
            try:
                import_file = open(options.import_from, 'r')
            except IOError:
                parser.error('Could not open XML data file %r'
                             % options.import_from)
            db = schevo.database.open(
                db_filename, schema_source, initialize=False)
            from schevoxml import ImporterTransaction
            tx = ImporterTransaction(import_file)
            db.execute(tx)
            import_file.close()
        else:
            db = schevo.database.open(db_filename, schema_source)
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
        db.close()
        print 'Database created.'


start = Create


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
