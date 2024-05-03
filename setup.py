import os
import re
import subprocess
from setuptools import setup, find_packages, Command

from mike.app_version import version

root_dir = os.path.abspath(os.path.dirname(__file__))


class Coverage(Command):
    description = 'run tests with code coverage'
    user_options = [
        ('test-suite=', 's',
         "test suite to run (e.g. 'some_module.test_suite')"),
    ]

    def initialize_options(self):
        self.test_suite = None

    def finalize_options(self):
        pass

    def run(self):
        env = dict(os.environ)
        pythonpath = os.path.join(root_dir, 'test', 'scripts')
        if env.get('PYTHONPATH'):
            pythonpath += os.pathsep + env['PYTHONPATH']
        env.update({
            'PYTHONPATH': pythonpath,
            'COVERAGE_FILE': os.path.join(root_dir, '.coverage'),
            'COVERAGE_PROCESS_START': os.path.join(root_dir, 'setup.cfg'),
        })

        subprocess.run(['coverage', 'erase'], check=True)
        subprocess.run(
            ['coverage', 'run', 'setup.py', 'test'] +
            (['-q'] if self.verbose == 0 else []) +
            (['-s', self.test_suite] if self.test_suite else []),
            env=env, check=True
        )
        subprocess.run(['coverage', 'combine'], check=True,
                       stdout=subprocess.DEVNULL)


custom_cmds = {
    'coverage': Coverage,
}

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# mike)\n\n(.+\n)*', r'\1', f.read())

setup(
    name='mike',
    version=version,

    description=('Manage multiple versions of your MkDocs-powered ' +
                 'documentation'),
    long_description=long_desc,
    long_description_content_type='text/markdown',
    keywords='mkdocs multiple versions',
    url='https://github.com/jimporter/mike',

    author='Jim Porter',
    author_email='itsjimporter@gmail.com',
    license='BSD-3-Clause',

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',

        'Topic :: Documentation',
        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    packages=find_packages(exclude=['test', 'test.*']),
    include_package_data=True,

    install_requires=(['importlib_metadata', 'importlib_resources',
                       'jinja2 >= 2.7', 'mkdocs >= 1.0', 'pyparsing >= 3.0',
                       'pyyaml >= 5.1', 'pyyaml_env_tag', 'verspec']),
    extras_require={
        'dev': ['coverage', 'flake8 >= 3.0', 'flake8-quotes', 'shtab'],
        'test': ['coverage', 'flake8 >= 3.0', 'flake8-quotes', 'shtab'],
    },

    entry_points={
        'console_scripts': [
            'mike = mike.driver:main',
        ],
        'mkdocs.plugins': [
            'mike = mike.mkdocs_plugin:MikePlugin',
        ],
        'mike.themes': [
            'mkdocs = mike.themes.mkdocs',
            'readthedocs = mike.themes.readthedocs',

            # Bootswatch themes
            'bootstrap = mike.themes.mkdocs',
            'cerulean = mike.themes.mkdocs',
            'cosmo = mike.themes.mkdocs',
            'cyborg = mike.themes.mkdocs',
            'darkly = mike.themes.mkdocs',
            'flatly = mike.themes.mkdocs',
            'journal = mike.themes.mkdocs',
            'litera = mike.themes.mkdocs',
            'lumen = mike.themes.mkdocs',
            'lux = mike.themes.mkdocs',
            'materia = mike.themes.mkdocs',
            'minty = mike.themes.mkdocs',
            'pulse = mike.themes.mkdocs',
            'sandstone = mike.themes.mkdocs',
            'simplex = mike.themes.mkdocs',
            'slate = mike.themes.mkdocs',
            'solar = mike.themes.mkdocs',
            'spacelab = mike.themes.mkdocs',
            'superhero = mike.themes.mkdocs',
            'united = mike.themes.mkdocs',
            'yeti = mike.themes.mkdocs',

            # Bootswatch classic themes
            'amelia = mike.themes.mkdocs',
            'readable = mike.themes.mkdocs',
            'mkdocs-classic = mike.themes.mkdocs',
            'amelia-classic = mike.themes.mkdocs',
            'bootstrap-classic = mike.themes.mkdocs',
            'cerulean-classic = mike.themes.mkdocs',
            'cosmo-classic = mike.themes.mkdocs',
            'cyborg-classic = mike.themes.mkdocs',
            'flatly-classic = mike.themes.mkdocs',
            'journal-classic = mike.themes.mkdocs',
            'readable-classic = mike.themes.mkdocs',
            'simplex-classic = mike.themes.mkdocs',
            'slate-classic = mike.themes.mkdocs',
            'spacelab-classic = mike.themes.mkdocs',
            'united-classic = mike.themes.mkdocs',
            'yeti-classic = mike.themes.mkdocs',
        ],
    },

    test_suite='test',
    cmdclass=custom_cmds,
    zip_safe=False,
)
