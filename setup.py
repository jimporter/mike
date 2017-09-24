import os
from setuptools import setup, find_packages
from six import iteritems

from mkultra.app_version import version

custom_cmds = {}

try:
    from flake8.main.setuptools_command import Flake8

    class LintCommand(Flake8):
        def distribution_files(self):
            return ['setup.py', 'mkultra']

    custom_cmds['lint'] = LintCommand
except:
    pass

with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
    long_desc = f.read()

try:
    import pypandoc
    long_desc = pypandoc.convert(long_desc, 'rst', format='md')
except ImportError:
    pass

setup(
    name='mkultra',
    version=version,

    description=('Manage multiple versions of your MkDocs-powered ' +
                 'documentation'),
    long_description=long_desc,
    keywords='mkdocs multiple versions',
    url='https://github.com/jimporter/mkultra',

    author='Jim Porter',
    author_email='porterj@alum.rit.edu',
    license='BSD',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',

        'Topic :: Documentation',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    packages=find_packages(exclude=['test', 'test.*']),

    install_requires=(['mkdocs', 'setuptools', 'six']),
    extras_require={
        'dev': ['flake8 >= 3.0', 'pypandoc'],
    },

    entry_points={
        'console_scripts': [
            'mkultra=mkultra.driver:main',
        ],
    },

    cmdclass=custom_cmds,
)
