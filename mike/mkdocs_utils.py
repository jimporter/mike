import os
import re
import subprocess
import yaml
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

docs_version_var = 'MIKE_DOCS_VERSION'


class ConfigData:
    def __init__(self, config_file):
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.Loader)
        self.site_dir = os.path.join(os.path.dirname(config_file),
                                     config.get('site_dir', 'site'))
        self.remote_name = config.get('remote_name', 'origin')
        self.remote_branch = config.get('remote_branch', 'gh-pages')
        self.use_directory_urls = config.get('use_directory_urls', True)


@contextmanager
def inject_plugin(config_file):
    with open(config_file) as f:
        config = yaml.load(f, Loader=yaml.Loader)

    plugins = config.setdefault('plugins', ['search'])
    for i in plugins:
        if ( (isinstance(i, str) and i == 'mike') or
             (isinstance(i, dict) and 'mike' in i) ):
            yield config_file
            return

    plugins.insert(0, 'mike')
    with NamedTemporaryFile(mode='w', dir=os.path.dirname(config_file),
                            prefix='mike-mkdocs', suffix='.yml',
                            delete=False) as f:
        yaml.dump(config, f)

    try:
        yield f.name
    finally:
        os.remove(f.name)


def build(config_file, version, verbose=True):
    command = (
        ['mkdocs', 'build', '--clean'] +
        (['--config-file', config_file] if config_file else [])
    )

    env = os.environ.copy()
    env[docs_version_var] = version

    output = None if verbose else subprocess.DEVNULL
    subprocess.run(command, check=True, env=env, stdout=output, stderr=output)


def version():
    output = subprocess.run(
        ['mkdocs', '--version'],
        check=True, stdout=subprocess.PIPE, universal_newlines=True
    ).stdout.rstrip()
    m = re.search('^mkdocs, version (\\S*)', output)
    return m.group(1)
