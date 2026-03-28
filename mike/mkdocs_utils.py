import os
import subprocess
from zensical.config import parse_config
from collections.abc import Iterable
from contextlib import contextmanager

docs_version_var = 'MIKE_DOCS_VERSION'

def _open_config(config_file=None):
    if config_file is None:
        config_file = ['zensical.toml', 'mkdocs.yml', 'mkdocs.yaml']
    elif not isinstance(config_file, Iterable) or isinstance(config_file, str):
        config_file = [config_file]

    exc = None
    for file in config_file:
        try:
            with open(file, encoding="utf-8"):
                pass
            return file
        except FileNotFoundError as e:
            if not exc:
                exc = e
    raise exc


def load_config(config_file=None, **kwargs):
    config_file = _open_config(config_file)
    return parse_config(config_file)

@contextmanager
def inject_plugin(config_file):
    # We do not need to inject the plugin for Zensical
    yield _open_config(config_file)


def build(config_file, version, *, quiet=False, output=None):
    command = (
        ['zensical', 'build', '--clean'] +
        (['--config-file', config_file] if config_file else [])
    )

    env = os.environ.copy()
    env[docs_version_var] = version

    subprocess.run(command, check=True, env=env, stdout=output, stderr=output)


def version():
    output = subprocess.run(
        ['zensical', '--version'],
        check=True, stdout=subprocess.PIPE, universal_newlines=True
    ).stdout.rstrip()
    return output
