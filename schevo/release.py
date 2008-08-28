from textwrap import dedent

from setuptools import Extension, find_packages

from paver.runtime import Bunch


setup_meta = Bunch(
    name='Schevo',
    version='3.1a2',
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
    <http://github.com/gldnspud/schevo/tarball/master#egg=Schevo-dev>`__.
    """),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
            'GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development :: Libraries :: '
            'Application Frameworks',
    ],
    keywords='database dbms',
    author='Orbtech, L.L.C. and contributors',
    author_email='schevo@googlegroups.com',
    url='http://schevo.org/',
    license='LGPL',
    packages=find_packages(exclude=['doc', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Louie >= 1.1',
        'PasteScript >= 1.6.1.1',
        'SchevoDurus >= 3.1a1',
    ],
    tests_require=['nose >= 0.10.1'],
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
    schevo.store = schevo.store.backend:SchevoStoreBackend

    [schevo.schevo_command]
    backends = schevo.script.backends:start
    db = schevo.script.db:start
    shell = schevo.script.shell:start
    """,
)