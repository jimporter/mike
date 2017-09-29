import os
from pkg_resources import iter_entry_points
import ruamel.yaml as yaml
from ruamel.yaml.util import load_yaml_guess_indent
import shutil

from . import git_utils
from . import mkdocs
from .app_version import version as app_version
from .versions import Versions


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def deploy(site_dir, version, aliases=[], branch='gh-pages', message=None):
    if message is None:
        message = (
            'Deployed {rev} to {doc_version} with MkDocs {mkdocs_version} ' +
            'and mkultra {mkultra_version}'
        ).format(
            rev=git_utils.get_latest_commit('HEAD'),
            doc_version=version,
            mkdocs_version=mkdocs.version(),
            mkultra_version=app_version
        )

    destdirs = [version] + aliases

    all_versions = Versions.load_from_git(branch)
    all_versions.add(version, aliases)

    commit = git_utils.Commit(branch, message)
    commit.delete_files(destdirs)

    for f in git_utils.walk_files(site_dir, destdirs):
        commit.add_file_data(f)
    commit.add_file_data(all_versions.to_file_info())
    commit.add_file_data(make_nojekyll())

    commit.finish()


def delete(version=None, all=False, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Removed {doc_version} with mkultra {mkultra_version}'
        ).format(
            doc_version='everything' if args.all else ', '.join(version),
            mkultra_version=app_version
        )

    if all:
        commit = git_utils.Commit(branch, message)
        commit.delete_files('*')
        commit.finish()
    elif version:
        all_versions = Versions.load_from_git(branch)
        all_versions.difference_update(version)

        commit = git_utils.Commit(branch, message)
        commit.delete_files(version)
        commit.add_file_data(all_versions.to_file_info())
        commit.finish()
    else:
        raise ValueError('specify `version` or `all`')


def list_versions(branch='gh-pages'):
    return Versions.load_from_git(branch)


def get_theme_dir(theme_name):
    if theme_name is None:
        raise ValueError('no theme specified')
    themes = list(iter_entry_points('mkultra.themes', theme_name))
    if len(themes) == 0:
        raise ValueError('no theme found')
    return os.path.dirname(themes[0].load().__file__)


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
            if not files:
                continue

            extras = config.setdefault(prop, [])
            for f in files:
                relpath = os.path.join(path, f)
                shutil.copyfile(os.path.join(theme_dir, relpath),
                                os.path.join(docs_dir, relpath))
                if relpath not in extras:
                    extras.append(relpath)
    yaml.round_trip_dump(config, open(mkdocs_yml, 'w'), indent=indent,
                         block_seq_indent=bsi)
