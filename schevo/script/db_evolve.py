"""Evolve database command.

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
schevo db evolve [options] DBFILE VERSION

DBFILE: The database file to evolve.

VERSION: The version of the schema to evolve to.  The database will be
evolved as many times as necessary to reach the version specified.
Specifying 'latest' causes the database to be evolved to the latest
schema version available.

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


class Evolve(Command):

    name = 'Evolve Database'
    description = 'Evolve an existing database.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 2:
            parser.error('Please specify both DBFILE and VERSION.')
        db_filename, final_version = args
        final_version = final_version.lower()
        if final_version != 'latest':
            try:
                final_version = int(final_version)
            except ValueError:
                parser.error('Please specify a version number or "latest".')
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
        db = schevo.database.open(db_filename)
        print 'Current database version is %i.' % db.version
        if final_version == 'latest':
            final_version = schevo.schema.latest_version(schema_path)
        evolve_db(parser, schema_path, db, final_version)
        # Import icons.
        if icon_path and os.path.exists(icon_path):
            print 'Importing icons...'
            schevo.icon.install(db, icon_path)
        # Pack the database.
        print 'Packing the database...'
        db.pack()
        # Done.
        db.close()
        print 'Database created.'


start = Evolve


def evolve_db(parser, schema_path, db, final_version):
    if final_version <= db.version:
        db.close()
        parser.error('Version specified is <= current database version.')
    latest_version = schevo.schema.latest_version(schema_path)
    if final_version == db.version:
        print 'Database is already at latest version.'
        return 0
    # Read schemata necessary for evolution.
    version = db.version + 1
    schemata_source = {}
    while version <= final_version:
        try:
            source = schevo.schema.read(schema_path, version=version)
        except schevo.error.SchemaFileIOError:
            parser.error('Could not read version %i' % version)
        schemata_source[version] = source
        print 'Read schema source for version %i.' % version
        version += 1
    versions = sorted(schemata_source.keys())
    # Evolve database.
    for version in versions:
        print 'Evolving database to version %i...' % version
        source = schemata_source[version]
        try:
            db._evolve(source, version)
        except:
            print 'Evolution to version %i failed.' % version
            print 'Database was left at version %i.' % db.version
            print 'Traceback of evolution failure follows.'
            db.close()
            raise
    print 'Database evolution to version %i complete.' % db.version


# Copyright (C) 2001-2006 Orbtech, L.L.C.
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
