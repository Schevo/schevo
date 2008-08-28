import paver.doctools
import paver.setuputils

from schevo.release import setup_meta


options(
    setup=setup_meta,
    sphinx=Bunch(
        docroot='doc',
        builddir='build',
        sourcedir='source',
    ),
)


@task
@needs('paver.doctools.html')
def openhtml():
    index_file = path('doc/build/html/index.html')
    sh('open ' + index_file)
