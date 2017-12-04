from __future__ import unicode_literals

import errno
import os
import ruamel.yaml as yaml
import shutil
from jinja2 import Template
from pkg_resources import iter_entry_points, resource_stream
from ruamel.yaml.util import load_yaml_guess_indent

from . import git_utils
from . import mkdocs
from .app_version import version as app_version
from .versions import Versions

versions_file = 'versions.json'


def list_versions(branch='gh-pages'):
    try:
        return Versions.loads(git_utils.read_file(
            branch, versions_file, universal_newlines=True
        ))
    except ValueError:
        return Versions()


def versions_to_file_info(versions):
    return git_utils.FileInfo(versions_file, versions.dumps())


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def deploy(site_dir, version, title=None, aliases=[], branch='gh-pages',
           message=None):
    if message is None:
        message = (
            'Deployed {rev} to {doc_version} with MkDocs {mkdocs_version} ' +
            'and mike {mike_version}'
        ).format(
            rev=git_utils.get_latest_commit('HEAD'),
            doc_version=version,
            mkdocs_version=mkdocs.version(),
            mike_version=app_version
        )

    destdirs = [version] + aliases

    all_versions = list_versions(branch)
    all_versions.add(version, title, aliases)

    commit = git_utils.Commit(branch, message)
    commit.delete_files(destdirs)

    for f in git_utils.walk_files(site_dir, destdirs):
        commit.add_file(f)
    commit.add_file(versions_to_file_info(all_versions))
    commit.add_file(make_nojekyll())

    commit.finish()


def delete(versions=None, all=False, branch='gh-pages', message=None):
    if not all and versions is None:
        raise ValueError('specify `version` or `all`')

    if message is None:
        message = (
            'Removed {doc_version} with mike {mike_version}'
        ).format(
            doc_version='everything' if all else ', '.join(versions),
            mike_version=app_version
        )

    commit = git_utils.Commit(branch, message)
    if all:
        commit.delete_files('*')
    else:
        all_versions = list_versions(branch)
        all_versions.difference_update(versions)

        commit.delete_files(versions)
        commit.add_file(versions_to_file_info(all_versions))
    commit.finish()


def rename(version, title, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Set title of version {version} to {title} with mike ' +
            '{mike_version}'
        ).format(version=version, title=title, mike_version=app_version)

    commit = git_utils.Commit(branch, message)
    all_versions = list_versions(branch)
    all_versions.rename(version, title)
    commit.add_file(versions_to_file_info(all_versions))
    commit.finish()


def set_default(version, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Set default version to {version} with mike ' +
            '{mike_version}'
        ).format(version=version, mike_version=app_version)

    all_versions = list_versions(branch)
    if not all_versions.find(version):
        raise ValueError('version {} not found'.format(version))

    commit = git_utils.Commit(branch, message)
    with resource_stream(__name__, 'templates/index.html') as f:
        t = Template(f.read().decode('utf-8'))
        commit.add_file(git_utils.FileInfo(
            'index.html', t.render(version=version)
        ))
    commit.finish()


def get_theme_dir(theme_name):
    if theme_name is None:
        raise ValueError('no theme specified')
    themes = list(iter_entry_points('mike.themes', theme_name))
    if len(themes) == 0:
        raise ValueError('no theme found')
    return os.path.dirname(themes[0].load().__file__)


def _makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise


def install_extras(mkdocs_yml, theme=None):
    with open(mkdocs_yml) as f:
        config, indent, bsi = load_yaml_guess_indent(f)
        if theme is None and 'theme' not in config:
            raise ValueError('no theme specified in mkdocs.yml; pass ' +
                             '--theme instead')
        theme_dir = get_theme_dir(config.get('theme', theme))
        docs_dir = config.get('docs_dir', 'docs')

        for path, prop in [('css', 'extra_css'), ('js', 'extra_javascript')]:
            files = os.listdir(os.path.join(theme_dir, path))
            if not files:  # pragma: no cover
                continue

            extras = config.setdefault(prop, [])
            for f in files:
                relpath = os.path.join(path, f)
                src = os.path.join(theme_dir, relpath)
                dst = os.path.join(docs_dir, relpath)

                _makedirs(os.path.dirname(dst))
                shutil.copyfile(src, dst)
                if relpath not in extras:
                    extras.append(relpath)

    with open(mkdocs_yml, 'w') as f:
        yaml.round_trip_dump(config, f, indent=indent, block_seq_indent=bsi)
