"""Create an empty schema (status: beta).

For copyright, license, and warranty, see bottom of file.
"""

import os
import shutil

import schevo.database
import schevo.icon

from schevo.script.command import Command
from schevo.script import opt

usage = """\
schevo db schema [options] DIRECTORY

DIRECTORY: The directory name which will contain the schema.

--app pointer to schevo application to copy schema from

The default schema used is "schevo.examples.blank"

development status: beta
This is an implementation beta, to be tested.

"""


def _parser():
    p = opt.parser(usage)

    p.add_option('-a', '--app', dest='app_path',
                 help='Use application in PATH.',
                 metavar='PATH',
                 default='schevo.example.blank',
                 )
    p.add_option('-s', '--schema', dest='schema_path',
                 help='Use schema in PATH.',
                 metavar='PATH',
                 default=None,
                 )
    return p


class Schema(Command):

    name = 'Create Schema'
    description = 'Create an empty schema.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if len(args) != 1:
            parser.error('Please specify DIRECTORY.')
        directory_name = args[0]
              
        # copied from db_inject:
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
            
        # implementation:
        os.mkdir(directory_name)        
        schema_dest = os.path.join(directory_name, 'schema')
        shutil.copytree(schema_path, schema_dest)
        
        print 'Created Schema from:\n' + schema_path
                

start = Schema


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
