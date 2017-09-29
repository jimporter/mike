import argparse
from pkg_resources import iter_entry_points
import ruamel.yaml as yaml
from ruamel.yaml.util import load_yaml_guess_indent
import os
import shutil

from . import git_utils
from . import mkdocs
from .app_version import version as app_version
from .versions import Versions


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def add_git_arguments(parser, commit=True):
    parser.add_argument('-r', '--remote', default='origin',
                        help='origin to push to (default: %(default)s)')
    parser.add_argument('-b', '--branch', default='gh-pages',
                        help='branch to commit to (default: %(default)s)')
    if (commit):
        parser.add_argument('-m', '--message',
                            help='commit message')
        parser.add_argument('-p', '--push', action='store_true',
                            help='push to {remote}/{branch} after commit')
        parser.add_argument('-f', '--force', action='store_true',
                            help='force push when pushing')


def deploy(args):
    if args.message:
        message = args.message
    else:
        message = (
            'Deployed {rev} to {doc_version} with MkDocs {mkdocs_version} ' +
            'and mkultra {mkultra_version}'
        ).format(
            rev=git_utils.get_latest_commit('HEAD'),
            doc_version=args.version,
            mkdocs_version=mkdocs.version(),
            mkultra_version=app_version
        )

    git_utils.update_branch(args.remote, args.branch)
    mkdocs.build()
    destdirs = [args.version] + args.alias

    all_versions = Versions.load_from_git(args.branch)
    all_versions.add(args.version, args.alias)

    commit = git_utils.Commit(args.branch, message)
    commit.delete_files(destdirs)

    for f in git_utils.walk_files(mkdocs.site_dir, destdirs):
        commit.add_file_data(f)
    commit.add_file_data(all_versions.to_file_info())
    commit.add_file_data(make_nojekyll())

    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def delete(args):
    if args.message:
        message = args.message
    else:
        message = (
            'Removed {doc_version} with mkultra {mkultra_version}'
        ).format(
            doc_version='everything' if args.all else ', '.join(args.version),
            mkultra_version=app_version
        )

    git_utils.update_branch(args.remote, args.branch)
    if args.all:
        commit = git_utils.Commit(args.branch, message)
        commit.delete_files('*')
        commit.finish()
    else:
        all_versions = Versions.load_from_git(args.branch)
        all_versions.difference_update(args.version)

        commit = git_utils.Commit(args.branch, args.message)
        commit.delete_files(args.version)
        commit.add_file_data(all_versions.to_file_info())
        commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def list_versions(args):
    git_utils.update_branch(args.remote, args.branch)
    all_versions = Versions.load_from_git(args.branch)
    for version, aliases in all_versions:
        if aliases:
            print("{version} ({aliases})".format(
                version=version, aliases=", ".join(aliases)
            ))
        else:
            print("{version}".format(version=version))


def get_theme_dir(theme_name):
    if theme_name is None:
        raise ValueError('no theme specified')
    themes = list(iter_entry_points('mkultra.themes', theme_name))
    if len(themes) == 0:
        raise ValueError('no theme found')
    return os.path.dirname(themes[0].load().__file__)


def install_extras(args):
    with open('mkdocs.yml') as f:
        config, indent, bsi = load_yaml_guess_indent(f)
        if not args.theme and 'theme' not in config:
            raise ValueError('no theme specified in mkdocs.yml; pass ' +
                             '--theme instead')
        theme_dir = get_theme_dir(config.get('theme', args.theme))
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
    yaml.round_trip_dump(config, open('mkdocs.yml', 'w'), indent=indent,
                         block_seq_indent=bsi)


def main():
    parser = argparse.ArgumentParser(prog='mkultra')
    subparsers = parser.add_subparsers()

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + app_version)

    deploy_p = subparsers.add_parser(
        'deploy', help='build docs and deploy them to a branch'
    )
    deploy_p.set_defaults(func=deploy)
    add_git_arguments(deploy_p)
    deploy_p.add_argument('version', metavar='VERSION',
                          help='version (directory) to deploy this build to')
    deploy_p.add_argument('alias', nargs='*', metavar='ALIAS',
                          help='alias for this build (e.g. "latest")')

    delete_p = subparsers.add_parser(
        'delete', help='delete docs from a branch'
    )
    delete_p.set_defaults(func=delete)
    add_git_arguments(delete_p)
    delete_p.add_argument('--all', action='store_true',
                          help='delete everything')
    delete_p.add_argument('version', nargs='*', metavar='VERSION',
                          help='version (directory) to delete')

    list_p = subparsers.add_parser(
        'list', help='list deployed docs on a branch'
    )
    list_p.set_defaults(func=list_versions)
    add_git_arguments(list_p, commit=False)

    install_extras_p = subparsers.add_parser(
        'install-extras', help='install extra files to your docs'
    )
    install_extras_p.set_defaults(func=install_extras)
    install_extras_p.add_argument('-t', '--theme',
                                  help='the theme to use for your docs')

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as e:
        parser.exit(1, '{prog}: {error}\n'.format(
            prog=parser.prog, error=str(e)
        ))
