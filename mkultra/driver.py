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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + app_version)
    parser.add_argument('-m', '--message', default='commit',
                        help='commit message')
    parser.add_argument('-D', '--delete', action='append', default=[],
                        help='files to delete')
    parser.add_argument('-r', '--remote', default='origin',
                        help='origin to push to [%(default)s]')
    parser.add_argument('-b', '--branch', default='gh-pages',
                        help='branch to commit to [%(default)s]')
    parser.add_argument('-p', '--push', action='store_true',
                        help='push to {remote}/{branch} after commit')
    parser.add_argument('-f', '--force', action='store_true',
                        help='force push when pushing')
    parser.add_argument('version', nargs='?', metavar='VERSION',
                        help='version (directory) to deploy this build to')
    parser.add_argument('alias', nargs='*', metavar='ALIAS',
                        help='alias for this build (e.g. "latest")')
    args = parser.parse_args()

    if not args.version and not args.delete:
        parser.error('must either add or remove a version')

    if args.version:
        run_mkdocs()

    all_versions = Versions.load_from_git(args.branch)
    all_versions.difference_update(args.delete)
    all_versions.add(args.version, args.alias)

    commit = git_utils.Commit(args.branch, args.message)
    commit.delete_files(args.delete)
    commit.delete_files(args.version)

    destdirs = [args.version] + args.alias
    for f in git_utils.walk_files(mkdocs_site_dir, destdirs):
        commit.add_file_data(f)
    commit.add_file_data(all_versions.to_file_info())
    commit.add_file_data(make_nojekyll())

    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)
