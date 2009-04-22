"""Description of module."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

from schevo.script.command import CommandSet
from schevo.script import (
    db_compare,
    db_convert,
    db_copy,
    db_create,
    db_evolve,
    db_inject,
    db_pack,
    db_repair,
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
            'evolve': db_evolve.start,
            'inject': db_inject.start,
            'pack': db_pack.start,
            'repair': db_repair.start,
            'update': db_update.start,
            }


start = Database
