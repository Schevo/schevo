__version__ = '3.0b4'

from setuptools import setup, Extension, find_packages
import sys, os
import textwrap

## import finddata

setup(
    name="Schevo",
    
    version=__version__,
    
    description="Next-generation DBMS",
    
    long_description=textwrap.dedent("""
    Schevo is a next-generation DBMS that focuses on the following:

    - **Database Integrity**: Schevo is designed from the ground up to
      protect your data.  All changes to a Schevo database must be
      done using transactions, and Schevo ensures that those
      transactions always leave the database in a consistent state.

    - **Rapid Development**: Schevo includes features to make it easy
      and fun to create even the most complex of databases.  Not only
      is the schema syntax easy to write and understand, you can also
      quickly place initial values in your schema that are required by
      your database, and use the same syntax to create sets of sample
      data to use during development.

    - **User Interface Generation**: Schevo provides user interface
      toolkits that take advantage of the richness of the database
      schema.  You can use the full-featured Schevo Navigator to
      interact with your database without writing a single line of
      code outside of your database schema.  A PyQt-based toolkit is
      already available, and various other toolkits, including a web
      toolkit, are in the works.

    - **Rich Schema Definition**: The schema for a Schevo database is
      written in concise, easy-to-read Python code.  Not only does the
      schema describe how information in the database is structured,
      but also defines all transactions and rules that ensure database
      integrity.

    - **Assisted Schema Evolution**: Once a Schevo database is
      deployed and is used to store valuable data, you will inevitably
      make further changes to the structure of the database.  Schevo
      assists you in this task and makes it easy to restructure a
      database and facilitate the migration of data from one schema
      version to the next.

    The latest development version is available in a `Subversion
    repository <http://schevo.org/svn/trunk/Schevo#egg=Schevo-dev>`__.
    """),
    
    classifiers=[
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Database :: Database Engines/Servers',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    
    keywords='database dbms',
    
    author='Orbtech, L.L.C. and contributors',
    author_email='schevo-devel@lists.schevo.org',

    url='http://schevo.org/trac/wiki/Schevo',
    
    license='LGPL',
    
    platforms=['UNIX', 'Windows'],

    packages=find_packages(exclude=['doc', 'tests']),

##     package_data=finddata.find_package_data(),

    zip_safe=False,
    
    install_requires=[
    'Louie >= 1.0',
    ],
    
    tests_require=[
    'nose >= 0.9.0',
    ],
    test_suite='nose.collector',
    
    extras_require={
    },
    
    dependency_links = [
    'http://schevo.org/files/thirdparty/',
    ],
    
    ext_modules = [
    Extension('schevo.store._persistent', ['schevo/store/_persistent.c']),
    ],

    entry_points = """
    [console_scripts]
    schevo = schevo.script.main:start
    schevo_hotshot = schevo.script.main:start_hotshot

    [paste.paster_create_template]
    schevo = schevo.paste:SchevoTemplate

    [schevo.schevo_command]
    db = schevo.script.db:start
    shell = schevo.script.shell:start

    [schevo.schema_export]
    icon=schevo.icon.schema
    identity=schevo.identity.schema
    """,
    )
