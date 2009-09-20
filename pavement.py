try:
    import paver
except ImportError:
    # Ignore pavement during tests.
    pass
else:
    from paver.easy import *
    import paver.misctasks
    import paver.setuputils
    from paver.setuputils import setup

    from textwrap import dedent

    from setuptools import Extension, find_packages

    from schevo.release import VERSION


    DOCVERSION = VERSION
    DEVELOPMENT = True


    # Use branch name if git information is available; otherwise, use
    # version number from setup_meta.
    if DEVELOPMENT:
        try:
            git_head_path = path('.git/HEAD')
            contents = git_head_path.open('rU').readline().strip()
            name, value = contents.split()
            BRANCH = value.split('/')[-1]
            if BRANCH != 'master':
                DOCVERSION += '-' + BRANCH
        except:
            pass
        DOCVERSION += '-dev'


    setup(
        name='Schevo',
        version=VERSION,
        description='Next-generation DBMS',
        long_description=dedent("""
        Schevo is a next-generation DBMS that focuses on the following:

        * **Rapid Development**.

          It's easy and fun to create even the most complex of
          databases. Easily write and understand schema syntax. Quickly
          place required initial data directly in your schema; use the
          same syntax to create sets of sample data for development use.

        * **Rich Schema Definition**.

          Write database schemata using concise, easy-to-read Python
          code. Your schema will describe not only database structure, but
          also all transactions and rules that ensure database integrity.

        * **Automated Schema Evolution**.

          Deploy a Schevo database and use it to store valuable data, then
          easily make further changes to the structure of the
          database. Use Schevo's tools to help restructure a database and
          safely migrate data from one schema version to the next.

        * **Transaction Based**.

          Schevo protects your data. Use transactions to make all changes
          to a Schevo database (it's the only way it allows you to!), and
          you can trust Schevo to ensure that your database is left in a
          consistent state at all times.

        * **User Interface Generation**.

          User interface code takes advantage of the richness of your
          database schema. Use a full-featured database navigator to
          interact with your database without writing a single line of
          code outside your database schema. Build customized UIs using
          Schevo-aware widgets and UI tools.

        You can also get the `latest development version
        <http://github.com/gldnspud/schevo/zipball/master#egg=Schevo-dev>`__.
        """),
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Database :: Database Engines/Servers',
            'Topic :: Software Development :: Libraries :: '
                'Application Frameworks',
        ],
        keywords='database dbms',
        author='ElevenCraft Inc.',
        author_email='schevo@googlegroups.com',
        url='http://www.schevo.org/',
        license='MIT',
        packages=find_packages(exclude=['doc', 'tests']),
        include_package_data=True,
        package_data={
            'schevo.test.icons': ['*.png'],
        },
        zip_safe=False,
        install_requires=[
            'SchevoDurus == dev, >= 3.1.0dev-20090919',
        ],
        extras_require={
            'notifications': ['Louie >= 1.1'],
            'templates': ['PasteScript >= 1.7.3'],
        },
        tests_require=['nose >= 0.10.4'],
        test_suite='nose.collector',
        ext_modules=[
            Extension('schevo.store._s_persistent',
                      ['schevo/store/_s_persistent.c']),
        ],
        entry_points = """
        [console_scripts]
        schevo = schevo.script.main:start
        schevo_hotshot = schevo.script.main:start_hotshot

        [paste.paster_create_template]
        schevo = schevo.template:SchevoTemplate

        [schevo.backend]
        schevostore = schevo.store.backend:SchevoStoreBackend

        [schevo.schevo_command]
        backends = schevo.script.backends:start
        db = schevo.script.db:start
        shell = schevo.script.shell:start
        """,
        )


    options(
        cog=Bunch(
            basdir='doc/source',
            includedir='doc/source',
            pattern='*.txt',
            beginspec='<==',
            endspec='==>',
            endoutput='<==end==>',
        ),
        publish=Bunch(
            username='schevo',
            server='web7.webfaction.com',
            path='/home2/schevo/schevo_docs/schevo/%s' % DOCVERSION,
        ),
        sphinx=Bunch(
            docroot='doc',
            builddir='build',
            sourcedir='source',
        ),
    )


    @task
    @needs('generate_setup', 'minilib', 'setuptools.command.sdist')
    def sdist():
        """Overrides sdist to make sure that our setup.py is generated."""
        pass


    try:
        import paver.doctools
    except ImportError:
        pass
    else:
        @task
        @needs(['paver.doctools.cog', 'paver.doctools.html', 'paver.doctools.uncog'])
        def html():
            pass


        @task
        @needs('html')
        def docs():
            import webbrowser
            index_file = path('doc/build/html/index.html')
            webbrowser.open('file://' + index_file.abspath())


        @task
        @needs(['paver.doctools.cog', 'paver.doctools.html', 'paver.doctools.uncog'])
        @cmdopts([("username=", "u", "Username for remote server"),
                  ("server=", "s", "Server to publish to"),
                  ("path=", "p", "Path to publish to")])
        def publish():
            src_path = path('doc/build/html') / '.'
            dest_path = path(options.path) / '.'
            # Create the remote directory and copy files to it.
            if options.username:
                server = '%s@%s' % (options.username, options.server)
            else:
                server = options.server
            if sys.platform == 'win32':
                sh('plink %s "mkdir -p %s"' % (server, options.path))
                sh('pscp -r -v -batch %s %s:%s' % (src_path, server, dest_path))
            else:
                sh('ssh %s "mkdir -p %s"' % (server, options.path))
                sh('rsync -zav --delete %s %s:%s' % (src_path, server, dest_path))


        @task
        def doctests():
            from paver.doctools import _get_paths
            import sphinx
            options.order('sphinx', add_rest=True)
            paths = _get_paths()
            sphinxopts = ['', '-b', 'doctest', '-d', paths.doctrees,
                paths.srcdir, paths.htmldir]
            ret = dry(
                "sphinx-build %s" % (" ".join(sphinxopts),), sphinx.main, sphinxopts)


        @task
        @needs(['doctests', 'nosetests'])
        def test():
            pass
