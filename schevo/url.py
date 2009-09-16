"""Provides :class:`~schevo.url.URL` for db connection specification."""

# Schevo is Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.
#
# This module is based on MIT-licensed work by the SqlAlchemy team, and is thus
# Copyright (c) 2005-2009 Michael Bayer, ElevenCraft Inc., and contributors.

import re, cgi, sys, urllib

import schevo.backend


class URL(object):
    """
    Represent the components of a URL used to connect to a database.

    This object is suitable to be passed directly to a
    :func:`schevo.database.open` call.  The fields of the URL are
    parsed from a string by :func:`make_url`.  the string format of
    the URL is an RFC-1738-style string.

    All initialization parameters are available as public attributes.

    :param backend_name: the name of the database backend.
      This name will correspond to an available Schevo backend.

    :param username: The user name.

    :param password: database password.

    :param host: The name of the host.

    :param port: The port number.

    :param database: The database name.

    :param query: A dictionary of options to be passed to the
      dialect and/or the DBAPI upon connect.
    """

    def __init__(self, backend_name, username=None, password=None,
                 host=None, port=None, database=None, query=None):
        self.backend_name = backend_name
        self.username = username
        self.password = password
        self.host = host
        if port is not None:
            self.port = int(port)
        else:
            self.port = None
        self.database = database
        self.query = query or {}

    def __str__(self):
        s = self.backend_name + "://"
        if self.username is not None:
            s += self.username
            if self.password is not None:
                s += ':' + urllib.quote_plus(self.password)
            s += "@"
        if self.host is not None:
            s += self.host
        if self.port is not None:
            s += ':' + str(self.port)
        if self.database is not None:
            s += '/' + self.database
        if self.query:
            keys = self.query.keys()
            keys.sort()
            s += '?' + "&".join("%s=%s" % (k, self.query[k]) for k in keys)
        return s

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return \
            isinstance(other, URL) and \
            self.backend_name == other.backend_name and \
            self.username == other.username and \
            self.password == other.password and \
            self.host == other.host and \
            self.database == other.database and \
            self.query == other.query

    def get_backend(self):
        """Return the Schevo database backend class corresponding to
        this URL's driver name.
        """
        return schevo.backend.backends[self.backend_name]

    def translate_connect_args(self, **kw):
        """Translate url attributes into a dictionary of connection arguments.

        Returns attributes of this url (`host`, `database`, `username`,
        `password`, `port`) as a plain dictionary.  The attribute names are
        used as the keys by default.  Unset or false attributes are omitted
        from the final dictionary.

        :param \**kw: Optional, alternate key names for url attributes.
        """

        translated = {}
        attribute_names = ['host', 'database', 'username', 'password', 'port']
        for sname in attribute_names:
            if sname in kw:
                name = kw[sname]
            else:
                name = sname
            if name is not None and getattr(self, sname, False):
                translated[name] = getattr(self, sname)
        return translated


def make_url(name_or_url):
    """Given a string or unicode instance, produce a new URL instance.

    The given string is parsed according to the RFC 1738 spec.  If an
    existing URL object is passed, just returns the object.
    """
    if isinstance(name_or_url, basestring):
        return _parse_rfc1738_args(name_or_url)
    else:
        return name_or_url


def _parse_rfc1738_args(name):
    pattern = re.compile(r'''
            (?P<name>[\w\+]+)://
            (?:
                (?P<username>[^:/]*)
                (?::(?P<password>[^/]*))?
            @)?
            (?:
                (?P<host>[^/:]*)
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<database>.*))?
            '''
            , re.X)

    m = pattern.match(name)
    if m is not None:
        components = m.groupdict()
        if components['database'] is not None:
            tokens = components['database'].split('?', 2)
            components['database'] = tokens[0]
            query = (len(tokens) > 1 and dict(cgi.parse_qsl(tokens[1]))) or None
            # Py2K
            if query is not None:
                query = dict((k.encode('ascii'), query[k]) for k in query)
            # end Py2K
        else:
            query = None
        components['query'] = query

        if components['password'] is not None:
            components['password'] = urllib.unquote_plus(components['password'])

        name = components.pop('name')
        return URL(name, **components)
    else:
        raise ValueError("Could not parse rfc1738 URL from string '%s'" % name)


def _parse_keyvalue_args(name):
    m = re.match( r'(\w+)://(.*)', name)
    if m is not None:
        (name, args) = m.group(1, 2)
        opts = dict(cgi.parse_qsl(args))
        return URL(name, *opts)
    else:
        return None

