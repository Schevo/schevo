"""Schevo identity schemata, primarily for use with schevo.gears.

Usage inside a schema::

  schevo.identity.schema.use()

For copyright, license, and warranty, see bottom of file.
"""


# All Schevo schema modules must have these lines.
from schevo.schema import *
schevo.schema.prep(locals())


import datetime


def _export(namespace, *args, **kw):
    g = globals()
    class SchevoIdVisit(g['SchevoIdVisit']):
        pass
    class SchevoIdVisitUser(g['SchevoIdVisitUser']):
        pass
    class SchevoIdGroup(g['SchevoIdGroup']):
        pass
    class SchevoIdGroupPermission(g['SchevoIdGroupPermission']):
        pass
    class SchevoIdPermission(g['SchevoIdPermission']):
        pass
    class SchevoIdUser(g['SchevoIdUser']):
        pass
    class SchevoIdUserGroup(g['SchevoIdUserGroup']):
        pass
    namespace.update({
        'SchevoIdVisit': SchevoIdVisit,
        'SchevoIdVisitUser': SchevoIdVisitUser,
        'SchevoIdGroup': SchevoIdGroup,
        'SchevoIdGroupPermission': SchevoIdGroupPermission,
        'SchevoIdPermission': SchevoIdPermission,
        'SchevoIdUser': SchevoIdUser,
        'SchevoIdUserGroup': SchevoIdUserGroup,
        })


# XXX: How to separate visitor and identity schemata?
class SchevoIdVisit(E.Entity):

    key = f.string()
    created = f.datetime(default=datetime.datetime.now)
    expires = f.datetime()

    _key(key)


class SchevoIdVisitUser(E.Entity):

    visit = f.entity('SchevoIdVisit')
    user = f.entity('SchevoIdUser')

    _key(visit)


class SchevoIdGroup(E.Entity):

    name = f.unicode()
    description = f.unicode()
    created = f.datetime(default=datetime.datetime.now)

    _key(name)

    _initial = [
        (u'admin', u'Administrators', DEFAULT),
        ]

    def x_permissions(self):
        """Return list of all permissions for this group."""
        return [gp.permission for gp in
                self.sys.links('SchevoIdGroupPermission', 'group')]

    def x_users(self):
        """Return list of all users belonging to this group."""
        return [ug.user for ug in
                self.sys.links('SchevoIdUserGroup', 'group')]


class SchevoIdGroupPermission(E.Entity):

    group = f.entity('SchevoIdGroup')
    permission = f.entity('SchevoIdPermission')

    _key(group, permission)

    _initial = [
        ((u'admin', ), (u'superuser', )),
        ]

    def __unicode__(self):
        return u'%s :: %s' % (self.group, self.permission)


class SchevoIdPermission(E.Entity):

    name = f.unicode()
    description = f.unicode()

    _key(name)

    _initial = [
        (u'superuser', u'Perform any task.'),
        ]

    def x_groups(self):
        return [gp.group for gp in
                self.sys.links('SchevoIdGroupPermission', 'permission')]


class SchevoIdUser(E.Entity):

    name = f.unicode()
    email_address = f.unicode(required=False)
    display_name = f.unicode(required=False)
    password = f.password()
    created = f.datetime(default=datetime.datetime.now)
    
    _key(name)

    _initial = [
        (u'admin', u'admin@localhost', u'Administrator', u'admin', DEFAULT),
        ]

    def x_groups(self):
        return [ug.group for ug in
                self.sys.links('SchevoIdUserGroup', 'user')]

    def x_permissions(self):
        permissions = set()
        for group in self.x.groups():
            permissions.update(group.x.permissions())
        return permissions


class SchevoIdUserGroup(E.Entity):

    user = f.entity('SchevoIdUser')
    group = f.entity('SchevoIdGroup')

    _key(user, group)

    def __str__(self):
        return u'%s :: %s' % (self.user, self.group)

    _initial = [
        ((u'admin', ), (u'admin', )),
        ]


# XXX: Backwards-compatibility.
import textwrap
preamble = textwrap.dedent(
    """
    from warnings import warn as _warn
    _warn('See http://lists.orbtech.com/pipermail/schevo-devel/'
    '2006-March/000568.html', DeprecationWarning)
    _import('Schevo', 'identity', 1)      
    """
    )
# /XXX


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
