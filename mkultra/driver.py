import argparse
import subprocess

from . import git_utils
from .app_version import version as app_version
from .versions import Versions

mkdocs_site_dir = 'site'


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def run_mkdocs():
    return subprocess.call(['mkdocs', 'build'])


def add_git_arguments(parser, commit=True):
    parser.add_argument('-r', '--remote', default='origin',
                        help='origin to push to (default: %(default)s)')
    parser.add_argument('-b', '--branch', default='gh-pages',
                        help='branch to commit to (default: %(default)s)')
    if (commit):
        parser.add_argument('-m', '--message', default='commit',
                            help='commit message')
        parser.add_argument('-p', '--push', action='store_true',
                            help='push to {remote}/{branch} after commit')
        parser.add_argument('-f', '--force', action='store_true',
                            help='force push when pushing')


def deploy(args):
    git_utils.update_branch(args.remote, args.branch)
    run_mkdocs()
    destdirs = [args.version] + args.alias

    all_versions = Versions.load_from_git(args.branch)
    all_versions.add(args.version, args.alias)

    commit = git_utils.Commit(args.branch, args.message)
    commit.delete_files(destdirs)

    for f in git_utils.walk_files(mkdocs_site_dir, destdirs):
        commit.add_file_data(f)
    commit.add_file_data(all_versions.to_file_info())
    commit.add_file_data(make_nojekyll())

    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def delete(args):
    git_utils.update_branch(args.remote, args.branch)
    if args.all:
        commit = git_utils.Commit(args.branch, args.message)
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

    args = parser.parse_args()
    return args.func(args)
