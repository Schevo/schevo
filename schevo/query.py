"""Query classes."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import operator
import sys
from schevo.lib import optimize

from schevo import base
from schevo.constant import UNASSIGNED
import schevo.error
from schevo import field
from schevo.fieldspec import FieldMap, FieldSpecMap
from schevo.label import label, plural
from schevo.lib.odict import odict
from schevo.meta import schema_metaclass
import schevo.namespace
from schevo.namespace import namespaceproperty
from schevo import queryns
from schevo.trace import log


# --------------------------------------------------------------------


QueryMeta = schema_metaclass('Q')


# --------------------------------------------------------------------


class Query(base.Query):
    """Simplest query possible, returning no results."""

    __metaclass__ = QueryMeta

    def __call__(self):
        """Shortcut to get to `_query_results` method."""
        return self._results()

    def _results(self):
        """Return a `Results` instance based on the current state of
        this query."""
        return results(())

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        """Return a human language representation of the query."""
        return repr(self)


class Simple(Query):
    """Simple query that wraps a callable and a unicode
    representation."""

    def __init__(self, fn, label):
        self._fn = fn
        self._label = label

    def _results(self):
        return results(self._fn())

    def __unicode__(self):
        return self._label


class Param(Query):
    """Parameterized query that has field definitions, and an optional
    object on which to operate."""

    __slots__ = ['_on', '_field_map', '_label',
                 '_f', '_h', '_s']

    _field_spec = FieldSpecMap()

    # Namespaces.
    f = namespaceproperty('f', instance=schevo.namespace.Fields)
    h = namespaceproperty('h', instance=queryns.ParamChangeHandlers)
    s = namespaceproperty('s', instance=queryns.ParamSys)

    # Deprecated namespaces.
    sys = namespaceproperty('s', instance=queryns.ParamSys)

    def __init__(self, *args, **kw):
        self._field_map = self._field_spec.field_map(instance=self)
        if args:
            self._on = args[0]
        else:
            self._on = None
        for name, value in kw.iteritems():
            setattr(self, name, value)

    def __getattr__(self, name):
        try:
            return self._field_map[name].get()
        except KeyError:
            msg = 'Field %r does not exist on %r.' % (name, self)
            raise AttributeError(msg)

    def __setattr__(self, name, value):
        if name.startswith('_') or len(name) == 1:
            return Query.__setattr__(self, name, value)
        else:
            self._field_map[name].set(value)

    def __repr__(self):
        if self._on:
            return '<%s query on %s>' % (self.__class__.__name__, self._on)
        else:
            return '<%s query>' % self.__class__.__name__

    def _getAttributeNames(self):
        """Return list of hidden attributes to extend introspection."""
        return sorted(self._field_map.keys())


class Exact(Param):
    """Parameterized query for an extent that uses ``find``."""

    __slots__ = Param.__slots__

    _label = 'Exact Matches'

    def __init__(self, extent, **kw):
        # NOTE: This deliberately does NOT call Param.__init__
        self._on = extent
        # First, use the fields defined in a subclass, if any.
        field_spec = FieldSpecMap(self._field_spec)
        field_map = self._field_map = field_spec.field_map(instance=self)
        # Next, update field_spec and fields based on extent.
        for name, FieldClass in extent.field_spec.iteritems():
            if name not in field_map:
                # Subclass all fields so they won't be constrained by
                # having __slots__ defined.  Convert fget fields to
                # non-fget, so we can query against them.
                class NoSlotsField(FieldClass):
                    fget = None
                    readonly = False
                    required = False
                NoSlotsField.__name__ = FieldClass.__name__
                FieldClass = NoSlotsField
                field_spec[name] = FieldClass
                field = field_map[name] = FieldClass(self)
                field._name = name
        for field in field_map.itervalues():
            field.assigned = False
        for name, value in kw.iteritems():
            setattr(self, name, value)
            field = field_map[name]
            field.assigned = True

    def _results(self):
        return results(self._on.find(**self._criteria))

    @property
    def _criteria(self):
        criteria = odict()
        for name, field in self.s.field_map().iteritems():
            if field.assigned:
                criteria[name] = field.get()
        return criteria

    def __unicode__(self):
        extent = self._on
        criteria = self._criteria
        if criteria:
            field_spec = self._on.field_spec
            criteria = [
                # (field label, value label)
                (label(field_spec[name]), unicode(self.f[name]))
                for name in criteria
                ]
            criteria = ', '.join(
                '%s == %s' % (field_label, value_label)
                for field_label, value_label
                in criteria
                )
            return u'%s where (%s)' % (plural(extent), criteria)
        else:
            return u'all %s' % plural(extent)


class Links(Query):
    """Query whose results are a call to `links` on an entity."""

    def __init__(self, entity, other_extent, other_field_name):
        self._entity = entity
        self._other_extent = other_extent
        self._other_field_name = other_field_name

    def _results(self):
        return results(self._entity.s.links(
            self._other_extent, self._other_field_name))


class MatchOperator(object):
    def __init__(self, name, label, oper=None):
        self.name = name
        self.label = label
        self.operator = oper
    def __repr__(self):
        return '<MatchOperator: %s>' % self.label

o_any = MatchOperator('any', u'is anything')
o_assigned = MatchOperator('assigned', u'has a value')
o_unassigned = MatchOperator('unassigned', u'has no value')

o_eq = MatchOperator('eq', u'==', operator.eq)
o_in = MatchOperator('in', u'in', operator.contains)
o_le = MatchOperator('le', u'<=', operator.le)
o_lt = MatchOperator('lt', u'<', operator.lt)
o_ge = MatchOperator('ge', u'>=', operator.ge)
o_gt = MatchOperator('gt', u'>', operator.gt)
o_ne = MatchOperator('ne', u'!=', operator.ne)

def _contains(a, b):
    if a is UNASSIGNED:
        return False
    else:
        return b in a
o_contains = MatchOperator('contains', u'contains', _contains)

def _startswith(a, b):
    if a is UNASSIGNED:
        return False
    else:
        return a.startswith(b)
o_startswith = MatchOperator('startswith', u'starts with', _startswith)

o_aliases = {
    '==': o_eq,
    '<=': o_le,
    '<': o_lt,
    '>=': o_ge,
    '>': o_gt,
    '!=': o_ne,
    'eq': o_eq,
    'le': o_le,
    'lt': o_lt,
    'ge': o_ge,
    'gt': o_gt,
    'ne': o_ne,
    'any': o_any,
    'assigned': o_assigned,
    'contains': o_contains,
    'in': o_in,
    'startswith': o_startswith,
    'unassigned': o_unassigned,
    }

class Match(Query):
    """Field match query."""

    def __init__(self, on, field_name, operator=o_eq, value=None,
                 FieldClass=None):
        """Create a new field match query.

        - ``on``: Extent or Results instance to match on.

        - ``field_name``: The field name to match on.

        - ``operator``: An object or string alias for the
          `MatchOperator` to use when matching.

        - ``value``: If not ``None``, the value to match for, or
          results to match in.

        - ``FieldClass``: If not ``None``, the field class to use to
          create the ``field`` attribute.  If ``None``, then ``on``
          must provide a Field class for ``field_name``.
        """
        self.on = on
        self.field_name = field_name
        if not FieldClass:
            FieldClass = getattr(on.f, field_name)
        # Subclass all fields so they won't be constrained by having
        # __slots__ defined.  Convert fget fields to non-fget, so we
        # can query against them.
        class NoSlotsField(FieldClass):
            fget = None
            readonly = False
            required = False
        NoSlotsField.__name__ = FieldClass.__name__
        FieldClass = NoSlotsField
        self.FieldClass = FieldClass
        self.operator = operator
        self.value = value

    def _results(self):
        on = self.on
        if isinstance(on, base.Query):
            on = on()
        operator = self.operator
        field_name = self.field_name
        value = self.value
        if operator is o_in:
            if isinstance(value, base.Query):
                value = value()
            value = frozenset(value)
            return results(
                obj for obj in on if getattr(obj, field_name) in value)
        else:
            if operator is o_any:
                return results(on)
            elif operator is o_assigned:
                return results(
                    obj for obj in on
                    if getattr(obj, field_name) is not UNASSIGNED)
            elif operator is o_unassigned:
                if isinstance(on, base.Extent):
                    kw = {field_name: UNASSIGNED}
                    return results(on.find(**kw))
                else:
                    return results(
                        obj for obj in on
                        if getattr(obj, field_name) is UNASSIGNED)
            if value is not None:
                field = self.FieldClass(self, field_name)
                field.set(value)
                value = field.get()
            if isinstance(on, base.Extent) and operator is o_eq:
                kw = {field_name: value}
                return results(on.find(**kw))
            elif operator.operator:
                oper = operator.operator
                def generator():
                    for obj in on:
                        a = getattr(obj, field_name)
                        b = value
                        try:
                            result = oper(a, b)
                        except TypeError:
                            # Cannot compare e.g. UNASSIGNED with
                            # datetime; assume no match.
                            continue
                        if result:
                            yield obj
                return results(generator())

    def _get_operator(self):
        return self._operator

    def _set_operator(self, operator):
        if isinstance(operator, basestring):
            self._operator = o_aliases[operator]
        else:
            self._operator = operator

    operator = property(_get_operator, _set_operator)

    @property
    def valid_operators(self):
        """Return a sequence of valid operators based on the
        FieldClass."""
        FieldClass = self.FieldClass
        valid = []
        if issubclass(FieldClass, field.Field):
            valid.append(o_any)
            valid.append(o_assigned)
            valid.append(o_unassigned)
            valid.append(o_eq)
            valid.append(o_ne)
        if issubclass(FieldClass, (field.String, field.Unicode)):
            valid.append(o_contains)
            valid.append(o_startswith)
        if not issubclass(FieldClass, field.Entity):
            valid.append(o_le)
            valid.append(o_lt)
            valid.append(o_ge)
            valid.append(o_gt)
        return tuple(valid)

    def __unicode__(self):
        FieldClass = self.FieldClass
        field = FieldClass(self, self.field_name)
        operator = self.operator
        on = self.on
        if isinstance(on, base.Extent):
            on_label = plural(on)
        else:
            on_label = unicode(on)
        s = u'%s where %s %s' % (
            on_label,
            label(field),
            label(self.operator),
            )
        if operator is not o_any:
            value = self.value
            if isinstance(value, Query):
                s += u' %s' % value
            else:
                field.set(value)
                s += u' %s' % field
        return s


class Intersection(Query):
    """The results common to all given queries.

    - ``queries``: A list of queries to intersect.
    """

    def __init__(self, *queries):
        self.queries = list(queries)

    def _results(self):
        assert log(1, 'called Intersection')
        resultset = None
        for query in self.queries:
            assert log(2, 'resultset is', resultset)
            assert log(2, 'intersecting with', query)
            s = set(query())
            if resultset is None:
                resultset = s
            else:
                resultset = resultset.intersection(s)
        assert log(2, 'resultset is finally', resultset)
        return results(frozenset(resultset))

    def __unicode__(self):
        if not self.queries:
            return u'the intersection of ()'
        last_on = None
        for query in self.queries:
            # Optimize length of string when results will be all
            # entities in an extent.
            if (isinstance(query, Match)
                and isinstance(query.on, base.Extent)
                and (query.on is last_on or not last_on)
                and (query.operator is o_any)
                ):
                last_on = query.on
                continue
            # Not a default query.
            return u'the intersection of (%s)' % (
                u', '.join(unicode(query) for query in self.queries)
                )
        # Was a default query.
        return u'all %s' % plural(last_on)

    @property
    def match_names(self):
        """The field names of immediate Match subqueries."""
        field_names = []
        for query in self.queries:
            if isinstance(query, Match):
                field_names.append(query.field_name)
        return field_names

    def remove_match(self, field_name):
        """Remove the the first immediate Match subquery with the
        given field name."""
        for query in self.queries:
            if isinstance(query, Match) and query.field_name == field_name:
                self.queries.remove(query)
                return
        raise schevo.error.FieldDoesNotExist(self, field_name)


class ByExample(Intersection):
    """Find by example query for a given extent."""

    _label = 'By Example'

    def __init__(self, extent, **kw):
        queries = []
        self.extent = extent
        for name, FieldClass in extent.field_spec.iteritems():
            # Make sure calculated fields are -not- calculated in the
            # match query.
            class NoSlotsField(FieldClass):
                fget = None
                readonly = False
                required = False
            NoSlotsField.__name__ = FieldClass.__name__
            match = Match(extent, name, 'any', FieldClass=NoSlotsField)
            if name in kw:
                match.value = kw[name]
                match.operator = '=='
            queries.append(match)
        Intersection.__init__(self, *queries)


class Union(Query):
    """One of each unique result in all given queries.

    - ``queries``: The list of queries to union.
    """

    def __init__(self, *queries):
        self.queries = list(queries)

    def _results(self):
        resultset = set()
        for query in self.queries:
            resultset.update(query())
        return results(frozenset(resultset))

    def __unicode__(self):
        return u'the union of (%s)' % (
            u', '.join(unicode(query) for query in self.queries)
            )


class Group(Query):
    """Group a query's Results into a list of Results instances,
    grouped by a field."""

    def __init__(self, query, field_name, FieldClass):
        self.query = query
        self.field_name = field_name
        self.FieldClass = FieldClass

    def _results(self):
        field_name = self.field_name
        groups = {}
        for result in self.query():
            key = getattr(result, field_name)
            L = groups.setdefault(key, [])
            L.append(result)
        return results(values for values in groups.itervalues())

    def __unicode__(self):
        field = self.FieldClass(self, self.field_name)
        return u'%s, grouped by %s' % (self.query, label(field))


class Min(Query):
    """The result of each group in a Group query's results that has
    the minimum value for a field."""

    def __init__(self, query, field_name, FieldClass=None):
        self.query = query
        self.field_name = field_name
        self.FieldClass = FieldClass

    def _results(self):
        def generator():
            field_name = self.field_name
            groups = self.query()
            for group in groups:
                min_result = None
                min_value = None
                for result in group:
                    value = getattr(result, field_name)
                    if min_result is None or value < min_value:
                        min_result = result
                        min_value = value
                if min_result is not None:
                    yield min_result
        return results(generator())

    def __unicode__(self):
        field = self.FieldClass(self, self.field_name)
        return u'results that have the minimum %s in each (%s)' % (
            label(field), self.query
            )


class Max(Query):
    """The result of each group in a Group query's results that has
    the maximum value for a field."""

    def __init__(self, query, field_name, FieldClass=None):
        self.query = query
        self.field_name = field_name
        self.FieldClass = FieldClass

    def _results(self):
        def generator():
            field_name = self.field_name
            groups = self.query()
            for group in groups:
                max_result = None
                max_value = None
                for result in group:
                    value = getattr(result, field_name)
                    if max_result is None or value > max_value:
                        max_result = result
                        max_value = value
                if max_result is not None:
                    yield max_result
        return results(generator())

    def __unicode__(self):
        field = self.FieldClass(self, self.field_name)
        return u'results that have the maximum %s in each (%s)' % (
            label(field), self.query
            )


# --------------------------------------------------------------------


def results(obj):
    """Return a decorated object based on ``obj`` that mixes in the
    `schevo.base.Results` type."""
    if isinstance(obj, frozenset):
        return ResultsFrozenset(obj)
    elif isinstance(obj, list):
        return ResultsList(obj)
    elif isinstance(obj, set):
        return ResultsSet(obj)
    elif isinstance(obj, tuple):
        return ResultsTuple(obj)
    else:
        return ResultsIterator(obj)


class ResultsFrozenset(frozenset, base.Results):
    pass

class ResultsList(list, base.Results):
    pass

class ResultsSet(set, base.Results):
    pass

class ResultsTuple(tuple, base.Results):
    pass

class ResultsIterator(base.Results):

    def __init__(self, orig):
        self._orig = orig

    def __iter__(self):
        return iter(self._orig)


base.classes_using_fields = base.classes_using_fields + (Param, )


optimize.bind_all(sys.modules[__name__])  # Last line of module.
