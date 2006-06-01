# XXX: Backwards-compatibility.
import inspect
import schevo.schema
def use():
    from warnings import warn
    warn('See http://schevo.org/lists/archives/schevo-devel/'
         '2006-March/000568.html', DeprecationWarning)
    globals = inspect.currentframe(1).f_globals
    schevo.schema._import('Schevo', 'icon', 1, _globals=globals)

from schevo.icon.schema import schema_001
preamble = schema_001.preamble
# /XXX
