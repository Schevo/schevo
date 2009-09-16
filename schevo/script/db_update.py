"""Update database command."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database
import schevo.error
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script import opt
from schevo.script.path import package_path


usage = """\
schevo db update [options] URL

URL: URL of the database file to update.

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
    p.add_option('-k', '--pack',
                 dest='pack',
                 help='Pack the database.',
                 action='store_true',
                 default=False,
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
        # Open the database.
        print 'Opening database...'
        db = schevo.database.open(url)
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
        if options.pack:
            # Pack the database.
            print 'Packing the database...'
            db.pack()
        # Done.
        db.close()
        print 'Database updated.'


start = Update
