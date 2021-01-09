import os
import re
import subprocess
from ruamel import yaml


def site_dir(config_file):
    with open(config_file) as f:
        config = yaml.load(f, Loader=yaml.Loader)
        site = config.get('site_dir', 'site')
    return os.path.join(os.path.dirname(config_file), site)


def build(config_file, verbose=True):
    command = (
        ['mkdocs', 'build', '--clean'] +
        (['--config-file', config_file] if config_file else [])
    )
    output = None if verbose else subprocess.DEVNULL
    subprocess.run(command, check=True, stdout=output, stderr=output)


def version():
    output = subprocess.run(
        ['mkdocs', '--version'],
        check=True, stdout=subprocess.PIPE, universal_newlines=True
    ).stdout.rstrip()
    m = re.search('^mkdocs, version (\\S*)', output)
    return m.group(1)
