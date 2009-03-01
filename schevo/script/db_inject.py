"""Inject schema into database."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import os

import schevo.database
import schevo.icon
import schevo.schema

from schevo.script.command import Command
from schevo.script import opt
from schevo.store.connection import Connection
from schevo.store.file_storage import FileStorage


usage = """\
schevo db inject [options] DBFILE

DBFILE: The database file to inject a schema into.

THIS IS A DANGEROUS COMMAND and should only be used when absolutely
necessary.  When injecting a new schema into a database, it should not
have any changes that alter the semantics of the schema.

Either --app or --schema must be given at a minimum.

This command will determine the schema version from DBFILE, then load
that version of the schema from the given schema package."""


def _parser():
    p = opt.parser(usage)
    p.add_option('-a', '--app', dest='app_path',
                 help='Use application in PATH.',
                 metavar='PATH',
                 default=None
                 )
    p.add_option('-s', '--schema', dest='schema_path',
                 help='Use schema in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    return p


class Inject(Command):

    name = 'Inject Schema'
    description = 'Inject schema into an existing database.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify DBFILE.')
        db_filename = args[0]
        if not os.path.isfile(db_filename):
            parser.error('Please specify a DBFILE that exists.')
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
        schema_path = None
        if options.app_path:
            app_path = path(options.app_path)
            schema_path = os.path.join(app_path, 'schema')
        if options.schema_path:
            schema_path = path(options.schema_path)
        # Inspect the database file to get its schema version.
        fs = FileStorage(db_filename)
        schema_version = Connection(fs).get_root()['SCHEVO']['version']
        fs.close()
        print 'Database is at version %i.' % schema_version
        # Inject the schema.
        schema_source = schevo.schema.read(schema_path, version=schema_version)
        schevo.database.inject(
            filename=db_filename,
            backend_name=options.backend_name,
            backend_args=options.backend_args,
            schema_source=schema_source,
            version=schema_version,
            )
        print 'Schema injected as version %i.' % schema_version


start = Inject
