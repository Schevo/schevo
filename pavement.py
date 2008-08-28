from schevo.release import setup_meta


# Use branch name if git information is available; otherwise, use
# version number from setup_meta.
try:
    git_head_path = path('.git/HEAD')
    contents = git_head_path.open('rU').readline().strip()
    name, value = contents.split()
    branch_or_version = value.split('/')[-1]
except:
    branch_or_version = setup_meta.version


options(
    setup=setup_meta,
    sphinx=Bunch(
        docroot='doc',
        builddir='build',
        sourcedir='source',
    ),
    publish=Bunch(
        username='schevo',
        server='web5.webfaction.com',
        path='/home2/schevo/schevo_docs/schevo/%s' % branch_or_version,
    ),
)


@task
@needs('paver.doctools.html')
@cmdopts([("username=", "u", "Username for remote server"),
          ("server=", "s", "Server to publish to"),
          ("path=", "p", "Path to publish to")])
def publish():
    src_path = path('doc/build/html') / '.'
    dest_path = path(options.path) / '.'
    # First create the remote directory.
    sh('ssh %s@%s "mkdir -p %s"'
       % (options.username, options.server, options.path))
    # Next use rsync to copy everything there.
    sh('rsync -zav --delete %s %s@%s:%s'
       % (src_path, options.username, options.server, dest_path))


try:
    import paver.doctools
except ImportError:
    pass
else:
    @task
    @needs('paver.doctools.html')
    def openhtml():
        index_file = path('doc/build/html/index.html')
        sh('open ' + index_file)
