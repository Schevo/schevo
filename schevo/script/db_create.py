"""Create database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script.db_evolve import evolve_db
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db create [options] URL

URL: URL of the database file to create.

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
            parser.error('Please specify URL.')
        url = args[0]
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
        # Use a default backend if one was not specified on the
        # command-line.
        if '://' not in url:
            url = 'durus:///%s' % url
        # Create the database.
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
        try:
            db = schevo.database.create(
                url,
                schema_source=schema_source,
                schema_version=evolve_from_version,
                )
        except schevo.error.DatabaseAlreadyExists:
            print 'ERROR: Database already exists.'
            print 'Use "schevo db update" or "schevo db evolve" commands to'
            print 'update or evolve an existing database.'
            return 1
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
